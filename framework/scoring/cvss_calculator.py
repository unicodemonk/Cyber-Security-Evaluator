"""
CVSS 3.1 Calculator for vulnerability scoring.

Implements CVSS 3.1 Base Score calculation for security vulnerabilities.
Reference: https://www.first.org/cvss/v3.1/specification-document
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class CVSSVector:
    """
    CVSS 3.1 Base Metrics.
    
    Reference: https://www.first.org/cvss/v3.1/specification-document
    """
    # Exploitability Metrics
    attack_vector: str  # N(etwork), A(djacent), L(ocal), P(hysical)
    attack_complexity: str  # L(ow), H(igh)
    privileges_required: str  # N(one), L(ow), H(igh)
    user_interaction: str  # N(one), R(equired)
    
    # Impact Metrics
    confidentiality: str  # N(one), L(ow), H(igh)
    integrity: str  # N(one), L(ow), H(igh)
    availability: str  # N(one), L(ow), H(igh)
    
    # Scope
    scope: str  # U(nchanged), C(hanged)


class CVSSCalculator:
    """
    CVSS 3.1 Base Score calculator.
    
    Calculates vulnerability severity scores based on CVSS 3.1 specification.
    """
    
    # CVSS 3.1 metric weights
    ATTACK_VECTOR = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2}
    ATTACK_COMPLEXITY = {"L": 0.77, "H": 0.44}
    PRIVILEGES_REQUIRED_UNCHANGED = {"N": 0.85, "L": 0.62, "H": 0.27}
    PRIVILEGES_REQUIRED_CHANGED = {"N": 0.85, "L": 0.68, "H": 0.50}
    USER_INTERACTION = {"N": 0.85, "R": 0.62}
    CONFIDENTIALITY = {"N": 0.0, "L": 0.22, "H": 0.56}
    INTEGRITY = {"N": 0.0, "L": 0.22, "H": 0.56}
    AVAILABILITY = {"N": 0.0, "L": 0.22, "H": 0.56}
    
    def __init__(self):
        """Initialize CVSS calculator."""
        pass
    
    def calculate_base_score(self, vector: CVSSVector) -> float:
        """
        Calculate CVSS 3.1 Base Score.
        
        Args:
            vector: CVSS vector with all metrics
            
        Returns:
            CVSS Base Score (0.0-10.0)
        """
        # Calculate Exploitability
        exploitability = self._calculate_exploitability(vector)
        
        # Calculate Impact
        impact = self._calculate_impact(vector)
        
        # Calculate Base Score
        if impact <= 0:
            return 0.0
        
        if vector.scope == "U":
            base_score = min(10.0, (impact + exploitability))
        else:  # Scope Changed
            base_score = min(10.0, 1.08 * (impact + exploitability))
        
        # Round up to one decimal
        return round(base_score, 1)
    
    def _calculate_exploitability(self, vector: CVSSVector) -> float:
        """Calculate Exploitability sub-score."""
        av = self.ATTACK_VECTOR[vector.attack_vector]
        ac = self.ATTACK_COMPLEXITY[vector.attack_complexity]
        
        # Privileges Required depends on Scope
        if vector.scope == "U":
            pr = self.PRIVILEGES_REQUIRED_UNCHANGED[vector.privileges_required]
        else:
            pr = self.PRIVILEGES_REQUIRED_CHANGED[vector.privileges_required]
        
        ui = self.USER_INTERACTION[vector.user_interaction]
        
        exploitability = 8.22 * av * ac * pr * ui
        return exploitability
    
    def _calculate_impact(self, vector: CVSSVector) -> float:
        """Calculate Impact sub-score."""
        c = self.CONFIDENTIALITY[vector.confidentiality]
        i = self.INTEGRITY[vector.integrity]
        a = self.AVAILABILITY[vector.availability]
        
        # Impact Sub-Score
        isc_base = 1 - ((1 - c) * (1 - i) * (1 - a))
        
        if vector.scope == "U":
            impact = 6.42 * isc_base
        else:  # Scope Changed
            impact = 7.52 * (isc_base - 0.029) - 3.25 * ((isc_base - 0.02) ** 15)
        
        return impact
    
    def get_severity_rating(self, score: float) -> str:
        """
        Get severity rating from CVSS score.
        
        Args:
            score: CVSS Base Score (0.0-10.0)
            
        Returns:
            Severity rating: CRITICAL, HIGH, MEDIUM, LOW, NONE
        """
        if score == 0.0:
            return "NONE"
        elif score < 4.0:
            return "LOW"
        elif score < 7.0:
            return "MEDIUM"
        elif score < 9.0:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def create_vector_string(self, vector: CVSSVector) -> str:
        """
        Create CVSS vector string.
        
        Args:
            vector: CVSS vector
            
        Returns:
            CVSS vector string (e.g., "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
        """
        return (
            f"CVSS:3.1/"
            f"AV:{vector.attack_vector}/"
            f"AC:{vector.attack_complexity}/"
            f"PR:{vector.privileges_required}/"
            f"UI:{vector.user_interaction}/"
            f"S:{vector.scope}/"
            f"C:{vector.confidentiality}/"
            f"I:{vector.integrity}/"
            f"A:{vector.availability}"
        )
    
    def calculate_from_attack_type(self, attack_type: str, impact_level: str = "HIGH") -> tuple[float, str]:
        """
        Calculate CVSS score from attack type with default assumptions.
        
        Args:
            attack_type: Type of attack (e.g., "command_injection", "prompt_injection")
            impact_level: Impact level (HIGH, MEDIUM, LOW)
            
        Returns:
            Tuple of (cvss_score, vector_string)
        """
        # Default vectors for common attack types
        vectors = {
            "command_injection": CVSSVector(
                attack_vector="N", attack_complexity="L",
                privileges_required="N", user_interaction="N",
                scope="U", confidentiality="H", integrity="H", availability="H"
            ),
            "prompt_injection": CVSSVector(
                attack_vector="N", attack_complexity="L",
                privileges_required="N", user_interaction="N",
                scope="C", confidentiality="L", integrity="H", availability="N"
            ),
            "role_confusion": CVSSVector(
                attack_vector="N", attack_complexity="L",
                privileges_required="N", user_interaction="R",
                scope="C", confidentiality="L", integrity="H", availability="N"
            ),
            "data_exfiltration": CVSSVector(
                attack_vector="N", attack_complexity="L",
                privileges_required="N", user_interaction="N",
                scope="U", confidentiality="H", integrity="N", availability="N"
            ),
            "privilege_escalation": CVSSVector(
                attack_vector="N", attack_complexity="L",
                privileges_required="L", user_interaction="N",
                scope="C", confidentiality="H", integrity="H", availability="H"
            ),
            "sql_injection": CVSSVector(
                attack_vector="N", attack_complexity="L",
                privileges_required="N", user_interaction="N",
                scope="U", confidentiality="H", integrity="H", availability="H"
            ),
            "xss": CVSSVector(
                attack_vector="N", attack_complexity="L",
                privileges_required="N", user_interaction="R",
                scope="C", confidentiality="L", integrity="L", availability="N"
            ),
        }
        
        # Get vector or use default
        vector = vectors.get(attack_type.lower(), CVSSVector(
            attack_vector="N", attack_complexity="L",
            privileges_required="N", user_interaction="N",
            scope="U", confidentiality="L", integrity="L", availability="L"
        ))
        
        # Adjust impact based on impact_level
        if impact_level == "MEDIUM":
            vector.confidentiality = "L" if vector.confidentiality == "H" else vector.confidentiality
            vector.integrity = "L" if vector.integrity == "H" else vector.integrity
            vector.availability = "L" if vector.availability == "H" else vector.availability
        elif impact_level == "LOW":
            vector.confidentiality = "L" if vector.confidentiality != "N" else "N"
            vector.integrity = "L" if vector.integrity != "N" else "N"
            vector.availability = "L" if vector.availability != "N" else "N"
        
        score = self.calculate_base_score(vector)
        vector_string = self.create_vector_string(vector)
        
        return score, vector_string
    
    def get_cwe_for_attack_type(self, attack_type: str) -> tuple[str, str]:
        """
        Get CWE ID and name for attack type.
        
        Args:
            attack_type: Type of attack
            
        Returns:
            Tuple of (cwe_id, cwe_name)
        """
        cwe_mapping = {
            "command_injection": ("CWE-77", "Improper Neutralization of Special Elements used in a Command"),
            "prompt_injection": ("CWE-94", "Improper Control of Generation of Code"),
            "role_confusion": ("CWE-269", "Improper Privilege Management"),
            "data_exfiltration": ("CWE-200", "Exposure of Sensitive Information to an Unauthorized Actor"),
            "privilege_escalation": ("CWE-269", "Improper Privilege Management"),
            "sql_injection": ("CWE-89", "Improper Neutralization of Special Elements used in an SQL Command"),
            "xss": ("CWE-79", "Improper Neutralization of Input During Web Page Generation"),
            "indirect_prompt_injection": ("CWE-913", "Improper Control of Dynamically-Managed Code Object"),
        }
        
        return cwe_mapping.get(attack_type.lower(), ("CWE-Other", "Other Vulnerability"))
