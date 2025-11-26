#!/usr/bin/env python3
"""
AgentBeats Controller Wrapper

This controller wraps A2A agents to provide:
1. State management and reset capabilities
2. Process lifecycle control (start/stop/restart)
3. Request proxying to the underlying agent
4. Reproducibility for AgentBeats assessments

The controller exposes an API for the AgentBeats platform to:
- Check agent status
- Reset agent to clean state before each assessment
- Start/stop the agent process
- Proxy requests to the agent
"""

import asyncio
import logging
import subprocess
import signal
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import uvicorn


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentState(str, Enum):
    """Agent process states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class ControllerConfig(BaseModel):
    """Configuration for the AgentBeats Controller."""
    agent_name: str
    agent_port: int
    agent_host: str = "127.0.0.1"
    launch_script: Optional[str] = None  # Path to run.sh or startup script
    launch_command: Optional[str] = None  # Direct command to start agent
    working_directory: Optional[str] = None
    startup_timeout: int = 30  # Seconds to wait for agent to start
    shutdown_timeout: int = 10  # Seconds to wait for graceful shutdown


class AgentStatus(BaseModel):
    """Current status of the agent."""
    state: AgentState
    pid: Optional[int] = None
    uptime_seconds: Optional[float] = None
    agent_url: str
    agent_card_url: str
    last_reset: Optional[str] = None
    error_message: Optional[str] = None


class ResetRequest(BaseModel):
    """Request to reset agent state."""
    hard_reset: bool = False  # If True, restart process; if False, try soft reset


class AgentBeatsController:
    """
    AgentBeats Controller for managing A2A agent lifecycle.
    
    This controller provides:
    - State management: Track agent process state
    - Reproducibility: Reset agent to clean state before assessments
    - Lifecycle control: Start, stop, restart agent process
    - Request proxying: Forward requests to the underlying agent
    """

    def __init__(self, config: ControllerConfig):
        """Initialize the controller."""
        self.config = config
        self.state = AgentState.STOPPED
        self.process: Optional[subprocess.Popen] = None
        self.start_time: Optional[float] = None
        self.last_reset: Optional[str] = None
        self.error_message: Optional[str] = None
        
        # Construct agent URLs
        self.agent_url = f"http://{config.agent_host}:{config.agent_port}"
        self.agent_card_url = f"{self.agent_url}/.well-known/agent-card.json"
        
        logger.info(f"AgentBeats Controller initialized for {config.agent_name}")
        logger.info(f"Agent URL: {self.agent_url}")

    async def start_agent(self) -> bool:
        """
        Start the agent process.
        
        Returns:
            True if agent started successfully, False otherwise
        """
        if self.state == AgentState.RUNNING:
            logger.warning("Agent is already running")
            return True

        self.state = AgentState.STARTING
        logger.info(f"Starting agent: {self.config.agent_name}")

        try:
            # Determine command to run
            if self.config.launch_script:
                # Use launch script (e.g., run.sh)
                script_path = Path(self.config.launch_script)
                if not script_path.exists():
                    raise FileNotFoundError(f"Launch script not found: {script_path}")
                
                command = [str(script_path.absolute())]
                logger.info(f"Using launch script: {script_path}")
            
            elif self.config.launch_command:
                # Use direct command
                command = self.config.launch_command.split()
                logger.info(f"Using launch command: {self.config.launch_command}")
            
            else:
                raise ValueError("No launch_script or launch_command configured")

            # Set working directory
            cwd = self.config.working_directory or os.getcwd()

            # Start the process
            self.process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group for clean shutdown
            )
            
            self.start_time = time.time()
            logger.info(f"Agent process started with PID: {self.process.pid}")

            # Wait for agent to be ready
            if await self._wait_for_agent_ready():
                self.state = AgentState.RUNNING
                logger.info(f"Agent {self.config.agent_name} is ready")
                return True
            else:
                self.state = AgentState.ERROR
                self.error_message = "Agent failed to become ready within timeout"
                logger.error(self.error_message)
                await self.stop_agent()
                return False

        except Exception as e:
            self.state = AgentState.ERROR
            self.error_message = str(e)
            logger.error(f"Failed to start agent: {e}")
            return False

    async def stop_agent(self) -> bool:
        """
        Stop the agent process.
        
        Returns:
            True if agent stopped successfully, False otherwise
        """
        if self.state == AgentState.STOPPED:
            logger.warning("Agent is already stopped")
            return True

        self.state = AgentState.STOPPING
        logger.info(f"Stopping agent: {self.config.agent_name}")

        try:
            if self.process:
                # Try graceful shutdown first (SIGTERM)
                logger.info(f"Sending SIGTERM to PID {self.process.pid}")
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                
                # Wait for graceful shutdown
                try:
                    self.process.wait(timeout=self.config.shutdown_timeout)
                    logger.info("Agent stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    logger.warning("Graceful shutdown timed out, forcing kill")
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    self.process.wait()
                    logger.info("Agent force killed")

                self.process = None
                self.start_time = None

            self.state = AgentState.STOPPED
            return True

        except Exception as e:
            self.state = AgentState.ERROR
            self.error_message = str(e)
            logger.error(f"Failed to stop agent: {e}")
            return False

    async def reset_agent(self, hard_reset: bool = False) -> bool:
        """
        Reset agent to clean state for reproducible assessments.
        
        Args:
            hard_reset: If True, restart the process; if False, try soft reset
        
        Returns:
            True if reset successful, False otherwise
        """
        logger.info(f"Resetting agent (hard_reset={hard_reset})")

        if hard_reset:
            # Hard reset: Restart the entire process
            logger.info("Performing hard reset (process restart)")
            if not await self.stop_agent():
                return False
            if not await self.start_agent():
                return False
        else:
            # Soft reset: Try to reset via agent's API (if supported)
            logger.info("Performing soft reset (API call)")
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Try common reset endpoints
                    reset_endpoints = ["/reset", "/api/reset", "/state/reset"]
                    
                    for endpoint in reset_endpoints:
                        try:
                            response = await client.post(f"{self.agent_url}{endpoint}")
                            if response.status_code == 200:
                                logger.info(f"Soft reset successful via {endpoint}")
                                self.last_reset = time.strftime("%Y-%m-%d %H:%M:%S")
                                return True
                        except httpx.HTTPStatusError:
                            continue
                    
                    # If no reset endpoint works, fall back to hard reset
                    logger.warning("No reset endpoint found, falling back to hard reset")
                    return await self.reset_agent(hard_reset=True)
                    
            except Exception as e:
                logger.error(f"Soft reset failed: {e}, falling back to hard reset")
                return await self.reset_agent(hard_reset=True)

        self.last_reset = time.strftime("%Y-%m-%d %H:%M:%S")
        return True

    async def _wait_for_agent_ready(self) -> bool:
        """
        Wait for agent to be ready (agent card accessible).
        
        Returns:
            True if agent is ready, False if timeout
        """
        logger.info(f"Waiting for agent to be ready (timeout: {self.config.startup_timeout}s)")
        
        start = time.time()
        async with httpx.AsyncClient() as client:
            while time.time() - start < self.config.startup_timeout:
                try:
                    response = await client.get(self.agent_card_url, timeout=2.0)
                    if response.status_code == 200:
                        logger.info("Agent card is accessible")
                        return True
                except (httpx.RequestError, httpx.HTTPStatusError):
                    pass
                
                await asyncio.sleep(1)
        
        logger.error(f"Agent did not become ready within {self.config.startup_timeout}s")
        return False

    async def proxy_request(self, path: str, method: str, headers: Dict, body: Any) -> Any:
        """
        Proxy a request to the underlying agent.
        
        Args:
            path: Request path
            method: HTTP method
            headers: Request headers
            body: Request body
        
        Returns:
            Raw response from agent (not wrapped)
        """
        if self.state != AgentState.RUNNING:
            raise HTTPException(status_code=503, detail="Agent is not running")

        url = f"{self.agent_url}{path}"
        logger.debug(f"Proxying {method} request to {url}")

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body if body else None
                )
                
                # Return raw response for transparent proxying
                # AgentBeats expects the actual agent card, not a wrapped response
                if response.headers.get("content-type", "").startswith("application/json"):
                    return response.json()
                else:
                    return response.text
        
        except Exception as e:
            logger.error(f"Proxy request failed: {e}")
            raise HTTPException(status_code=502, detail=f"Proxy error: {str(e)}")

    def get_status(self) -> AgentStatus:
        """Get current agent status."""
        uptime = None
        if self.start_time and self.state == AgentState.RUNNING:
            uptime = time.time() - self.start_time

        return AgentStatus(
            state=self.state,
            pid=self.process.pid if self.process else None,
            uptime_seconds=uptime,
            agent_url=self.agent_url,
            agent_card_url=self.agent_card_url,
            last_reset=self.last_reset,
            error_message=self.error_message
        )


def create_controller_app(controller: AgentBeatsController) -> FastAPI:
    """
    Create FastAPI app for the AgentBeats Controller.
    
    This exposes the controller API for the AgentBeats platform.
    """
    app = FastAPI(
        title=f"AgentBeats Controller - {controller.config.agent_name}",
        description="Controller for managing A2A agent lifecycle and state"
    )

    @app.get("/health")
    @app.head("/health")
    async def health_check():
        """
        Health check endpoint for AgentBeats platform.
        Returns 200 if controller is running and agent is accessible.
        Supports both GET and HEAD methods for AgentBeats online detection.
        """
        status = controller.get_status()
        if status.state == AgentState.RUNNING:
            return {
                "status": "healthy",
                "agent_state": status.state.value,
                "agent_accessible": True
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "agent_state": status.state.value,
                    "agent_accessible": False,
                    "error": status.error_message
                }
            )

    @app.get("/")
    async def launcher_health():
        """
        Root endpoint for launcher URL - provides agent identification (ID Preview).
        Returns agent metadata and launcher status for AgentBeats validation.
        """
        status = controller.get_status()
        return {
            "status": "online" if status.state == AgentState.RUNNING else "offline",
            "launcher": "ready" if status.state == AgentState.RUNNING else "not_ready",
            "agent": {
                "name": controller.config.agent_name,
                "url": controller.agent_url,
                "card_url": f"{controller.agent_url}/.well-known/agent-card.json",
                "state": status.state.value,
                "pid": status.pid,
                "uptime_seconds": status.uptime_seconds
            },
            "controller": {
                "version": "2.0.0",
                "endpoints": {
                    "health": "/health",
                    "status": "/status",
                    "start": "/start",
                    "stop": "/stop",
                    "reset": "/reset"
                }
            }
        }

    @app.get("/status")
    async def get_status():
        """
        Get current agent status in standard health check format.
        Returns 'pass' for healthy, 'fail' for unhealthy.
        """
        agent_status = controller.get_status()
        if agent_status.state == AgentState.RUNNING:
            return {
                "status": "server up, with agent running",
                "version": "2.0.0",
                "serviceId": controller.config.agent_name,
                "description": f"AgentBeats Controller for {controller.config.agent_name}",
                "checks": {
                    "agent": {
                        "status": "pass",
                        "componentType": "component",
                        "observedValue": agent_status.state.value,
                        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    }
                }
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "fail",
                    "version": "2.0.0",
                    "serviceId": controller.config.agent_name,
                    "output": agent_status.error_message or "Agent is not running",
                    "checks": {
                        "agent": {
                            "status": "fail",
                            "componentType": "component",
                            "observedValue": agent_status.state.value,
                            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        }
                    }
                }
            )

    @app.post("/start")
    async def start_agent():
        """Start the agent process."""
        success = await controller.start_agent()
        if success:
            return {"status": "success", "message": "Agent started"}
        else:
            raise HTTPException(status_code=500, detail="Failed to start agent")

    @app.post("/stop")
    async def stop_agent():
        """Stop the agent process."""
        success = await controller.stop_agent()
        if success:
            return {"status": "success", "message": "Agent stopped"}
        else:
            raise HTTPException(status_code=500, detail="Failed to stop agent")

    @app.post("/reset")
    async def reset_agent(request: ResetRequest):
        """Reset agent to clean state."""
        success = await controller.reset_agent(hard_reset=request.hard_reset)
        if success:
            return {"status": "success", "message": "Agent reset", "last_reset": controller.last_reset}
        else:
            raise HTTPException(status_code=500, detail="Failed to reset agent")

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"])
    async def proxy_to_agent(path: str, request: dict = None):
        """
        Proxy all other requests to the underlying agent.
        Supports HEAD method for AgentBeats online detection.
        """
        # This allows the controller to act as a transparent proxy
        # AgentBeats can call the controller URL, and it forwards to the agent
        return await controller.proxy_request(
            path=f"/{path}",
            method="POST",  # Simplified - in production, use request.method
            headers={},
            body=request
        )

    return app


async def main():
    """Main entry point for running the controller."""
    import argparse

    parser = argparse.ArgumentParser(description="AgentBeats Controller")
    parser.add_argument("--agent-name", required=True, help="Name of the agent")
    parser.add_argument("--agent-port", type=int, required=True, help="Port where agent runs")
    parser.add_argument("--agent-host", default="127.0.0.1", help="Host where agent runs")
    parser.add_argument("--controller-port", type=int, default=9000, help="Port for controller API")
    parser.add_argument("--launch-script", help="Path to agent launch script (run.sh)")
    parser.add_argument("--launch-command", help="Direct command to start agent")
    parser.add_argument("--working-dir", help="Working directory for agent")
    parser.add_argument("--auto-start", action="store_true", help="Auto-start agent on controller startup")

    args = parser.parse_args()

    # Create controller config
    config = ControllerConfig(
        agent_name=args.agent_name,
        agent_port=args.agent_port,
        agent_host=args.agent_host,
        launch_script=args.launch_script,
        launch_command=args.launch_command,
        working_directory=args.working_dir
    )

    # Create controller
    controller = AgentBeatsController(config)

    # Auto-start if requested
    if args.auto_start:
        logger.info("Auto-starting agent...")
        await controller.start_agent()

    # Create and run FastAPI app
    app = create_controller_app(controller)

    logger.info("=" * 70)
    logger.info(f"AgentBeats Controller - {args.agent_name}")
    logger.info("=" * 70)
    logger.info(f"Controller API: http://127.0.0.1:{args.controller_port}")
    logger.info(f"Launcher URL: http://127.0.0.1:{args.controller_port}")
    logger.info(f"Agent URL: {controller.agent_url}")
    logger.info(f"Agent Card: {controller.agent_card_url}")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Controller Endpoints:")
    logger.info(f"  GET  /health - Health check (for AgentBeats)")
    logger.info(f"  GET  /status - Get agent status")
    logger.info(f"  POST /start  - Start agent")
    logger.info(f"  POST /stop   - Stop agent")
    logger.info(f"  POST /reset  - Reset agent state")
    logger.info(f"  *    /*      - Proxy to agent")
    logger.info("=" * 70)
    logger.info("")
    logger.info("For AgentBeats Registration:")
    logger.info(f"  Use Launcher URL: http://YOUR_PUBLIC_IP:{args.controller_port}")
    logger.info("=" * 70)

    uvicorn_config = uvicorn.Config(app, host="0.0.0.0", port=args.controller_port)
    server = uvicorn.Server(uvicorn_config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
