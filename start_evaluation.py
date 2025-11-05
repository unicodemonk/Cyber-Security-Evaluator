"""
Start an evaluation using the A2A protocol.

This script demonstrates how to:
1. Submit a task to the Green Agent (Judge)
2. Poll for completion
3. Retrieve results

With both agents running:
- Purple Agent on http://127.0.0.1:8000
- Green Agent on http://127.0.0.1:9010

Run this script to trigger an evaluation.
"""

import asyncio
import httpx
import json
from datetime import datetime


async def start_evaluation():
    """Submit an evaluation task to the Green Agent via A2A protocol."""

    green_agent_url = "http://127.0.0.1:9010"
    purple_agent_url = "http://127.0.0.1:8000"

    print("=" * 70)
    print("🚀 Starting SQL Injection Detection Evaluation")
    print("=" * 70)
    print()

    # Step 1: Check Green Agent is ready
    print("1️⃣  Checking Green Agent status...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            card_response = await client.get(f"{green_agent_url}/card")
            card = card_response.json()
            print(f"   ✅ Green Agent: {card['name']}")
            print(f"   📋 Description: {card['description']}")
            print()
        except Exception as e:
            print(f"   ❌ Error: Green Agent not responding: {e}")
            return

    # Step 2: Check Purple Agent is ready
    print("2️⃣  Checking Purple Agent status...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            health_response = await client.get(f"{purple_agent_url}/health")
            print(f"   ✅ Purple Agent is healthy")
            print()
        except Exception as e:
            print(f"   ❌ Error: Purple Agent not responding: {e}")
            return

    # Step 3: Submit evaluation task via A2A protocol
    print("3️⃣  Submitting evaluation task to Green Agent...")

    # A2A protocol task structure
    task_payload = {
        "input": {
            "purple_agent_id": "baseline_sql_detector",
            "purple_agent_endpoint": purple_agent_url,
            "config": {
                "mode": "fixed",  # or "adaptive"
                "test_budget": 20,  # Number of tests to run
                "seed": 42
            },
            "metadata": {
                "evaluation_timestamp": datetime.now().isoformat(),
                "evaluator": "manual_trigger"
            }
        }
    }

    print(f"   📤 Task configuration:")
    print(f"      • Mode: {task_payload['input']['config']['mode']}")
    print(f"      • Test Budget: {task_payload['input']['config']['test_budget']}")
    print(f"      • Purple Agent: {task_payload['input']['purple_agent_id']}")
    print()

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Submit task
            task_response = await client.post(
                f"{green_agent_url}/tasks",
                json=task_payload
            )
            task_response.raise_for_status()
            task_data = task_response.json()
            task_id = task_data["id"]

            print(f"   ✅ Task submitted successfully!")
            print(f"   📝 Task ID: {task_id}")
            print(f"   ⏳ Status: {task_data.get('status', 'unknown')}")
            print()

            # Step 4: Poll for completion
            print("4️⃣  Waiting for evaluation to complete...")
            max_polls = 30
            poll_count = 0

            while poll_count < max_polls:
                poll_count += 1
                await asyncio.sleep(2)  # Poll every 2 seconds

                status_response = await client.get(f"{green_agent_url}/tasks/{task_id}")
                status_response.raise_for_status()
                status_data = status_response.json()

                current_status = status_data.get("status", "unknown")
                print(f"   ⏳ Poll {poll_count}: Status = {current_status}")

                if current_status == "completed":
                    print()
                    print("   ✅ Evaluation completed!")
                    print()

                    # Step 5: Display results
                    result = status_data.get("output", {})

                    print("=" * 70)
                    print("📊 EVALUATION RESULTS")
                    print("=" * 70)
                    print()

                    if result.get("success"):
                        metrics = result.get("metrics", {})

                        print("Overall Performance:")
                        print(f"  • F1 Score:          {metrics.get('f1_score', 0):.3f}")
                        print(f"  • Precision:         {metrics.get('precision', 0):.3f}")
                        print(f"  • Recall:            {metrics.get('recall', 0):.3f}")
                        print(f"  • Accuracy:          {metrics.get('accuracy', 0):.3f}")
                        print()

                        confusion = metrics.get('confusion_matrix', {})
                        print("Confusion Matrix:")
                        print(f"  • True Positives:    {confusion.get('true_positives', 0)}")
                        print(f"  • True Negatives:    {confusion.get('true_negatives', 0)}")
                        print(f"  • False Positives:   {confusion.get('false_positives', 0)}")
                        print(f"  • False Negatives:   {confusion.get('false_negatives', 0)}")
                        print()

                        print("Error Rates:")
                        print(f"  • False Positive Rate: {metrics.get('false_positive_rate', 0):.3f}")
                        print(f"  • False Negative Rate: {metrics.get('false_negative_rate', 0):.3f}")
                        print()

                        # Category breakdown
                        category_metrics = result.get("category_metrics", [])
                        if category_metrics:
                            print("Per-Category Performance:")
                            for cat_metric in category_metrics:
                                cat_name = cat_metric.get("category", "unknown")
                                cat_f1 = cat_metric.get("metrics", {}).get("f1_score", 0)
                                cat_count = cat_metric.get("sample_count", 0)
                                print(f"  • {cat_name:20s} | F1: {cat_f1:.3f} | Samples: {cat_count}")
                            print()

                        print("=" * 70)
                        print("✅ Evaluation Complete!")
                        print("=" * 70)
                    else:
                        error_msg = result.get("error_message", "Unknown error")
                        print(f"❌ Evaluation failed: {error_msg}")

                    break

                elif current_status == "failed":
                    print()
                    print(f"   ❌ Task failed!")
                    error = status_data.get("error", "Unknown error")
                    print(f"   Error: {error}")
                    break

            if poll_count >= max_polls:
                print()
                print(f"   ⚠️  Timeout: Task still running after {max_polls} polls")
                print(f"   You can check status manually: GET {green_agent_url}/tasks/{task_id}")

        except Exception as e:
            print(f"   ❌ Error during evaluation: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print()
    print("=" * 70)
    print("📋 SQL Injection Detection Evaluation via A2A Protocol")
    print("=" * 70)
    print()
    print("Prerequisites:")
    print("  ✓ Purple Agent running on http://127.0.0.1:8000")
    print("  ✓ Green Agent running on http://127.0.0.1:9010")
    print()
    print("This will:")
    print("  1. Submit an evaluation task to the Green Agent")
    print("  2. Green Agent will test the Purple Agent with 20 samples")
    print("  3. Display comprehensive metrics and results")
    print()
    input("Press ENTER to start evaluation...")
    print()

    asyncio.run(start_evaluation())
