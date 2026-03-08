import json
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import os


class IncidentAnalytics:
    """Analytics engine for incident replay and analysis"""
    
    def __init__(self, log_file='logs/incidents.jsonl'):
        self.log_file = log_file
    
    def load_incidents(self, days: int = 30) -> List[dict]:
        """Load incidents from log file"""
        incidents = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        
        if not os.path.exists(self.log_file):
            return incidents
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        incident = json.loads(line.strip())
                        incident_time = datetime.fromisoformat(incident['timestamp'])
                        if incident_time >= cutoff_time:
                            incidents.append(incident)
                    except (json.JSONDecodeError, KeyError):
                        continue
        except Exception as e:
            print(f"Error loading incidents: {e}")
        
        return incidents
    
    def replay_incident(self, incident_id: str) -> Optional[dict]:
        """Replay a specific incident with full timeline"""
        incidents = self.load_incidents(days=90)
        
        for incident in incidents:
            if incident.get('details', {}).get('incident_id') == incident_id:
                return {
                    'incident': incident,
                    'timeline': self._build_timeline(incident),
                    'attack_chain': self._reconstruct_attack_chain(incident),
                    'recommendations': self._generate_recommendations(incident)
                }
        
        return None
    
    def _build_timeline(self, incident: dict) -> List[dict]:
        """Build detailed timeline of incident"""
        timeline = []
        
        # Initial detection
        timeline.append({
            'time': incident['timestamp'],
            'event': 'Detection',
            'description': f"Threat detected: {incident.get('threat_level')}",
            'indicators': incident.get('indicators', [])
        })
        
        # Containment actions
        if incident.get('type') == 'containment':
            timeline.append({
                'time': incident['timestamp'],
                'event': 'Containment',
                'action': incident.get('action'),
                'success': incident.get('success')
            })
        
        return sorted(timeline, key=lambda x: x['time'])
    
    def _reconstruct_attack_chain(self, incident: dict) -> List[str]:
        """Reconstruct the attack chain"""
        chain = []
        
        indicators = incident.get('indicators', [])
        
        if 'decoy_file_compromised' in indicators:
            chain.append("Initial Access: Decoy file accessed")
        
        if 'high_entropy' in indicators:
            chain.append("Encryption: File encryption detected")
        
        if 'rapid_file_modifications' in indicators:
            chain.append("Impact: Mass file modification")
        
        if 'extension_changed' in indicators:
            chain.append("Execution: File extension changes")
        
        return chain
    
    def _generate_recommendations(self, incident: dict) -> List[str]:
        """Generate security recommendations based on incident"""
        recommendations = []
        
        threat_level = incident.get('threat_level', 'low')
        indicators = incident.get('indicators', [])
        
        if threat_level in ['critical', 'high']:
            recommendations.append("Immediate isolation of affected systems")
            recommendations.append("Forensic analysis of affected files")
            recommendations.append("Review and update backup procedures")
        
        if 'decoy_file_compromised' in indicators:
            recommendations.append("Deploy additional decoy files in strategic locations")
        
        if 'rapid_file_modifications' in indicators:
            recommendations.append("Implement stricter rate limiting on file operations")
            recommendations.append("Enable process monitoring and behavior analysis")
        
        recommendations.append("Update anti-malware signatures")
        recommendations.append("Conduct security awareness training")
        
        return recommendations
    
    def get_statistics(self, days: int = 7) -> dict:
        """Get analytics statistics"""
        incidents = self.load_incidents(days=days)
        
        stats = {
            'total_incidents': len(incidents),
            'by_severity': defaultdict(int),
            'by_type': defaultdict(int),
            'by_day': defaultdict(int),
            'most_common_indicators': defaultdict(int),
            'containment_success_rate': 0.0
        }
        
        containment_total = 0
        containment_success = 0
        
        for incident in incidents:
            # Severity
            severity = incident.get('threat_level', 'unknown')
            stats['by_severity'][severity] += 1
            
            # Type
            incident_type = incident.get('type', 'unknown')
            stats['by_type'][incident_type] += 1
            
            # Day
            incident_date = datetime.fromisoformat(incident['timestamp']).date()
            stats['by_day'][str(incident_date)] += 1
            
            # Indicators
            for indicator in incident.get('indicators', []):
                stats['most_common_indicators'][indicator] += 1
            
            # Containment success
            if incident_type == 'containment':
                containment_total += 1
                if incident.get('success'):
                    containment_success += 1
        
        if containment_total > 0:
            stats['containment_success_rate'] = (containment_success / containment_total) * 100
        
        # Convert defaultdicts to regular dicts
        stats['by_severity'] = dict(stats['by_severity'])
        stats['by_type'] = dict(stats['by_type'])
        stats['by_day'] = dict(stats['by_day'])
        stats['most_common_indicators'] = dict(
            sorted(stats['most_common_indicators'].items(), 
                   key=lambda x: x[1], 
                   reverse=True)[:10]
        )
        
        return stats
    
    def export_report(self, output_file: str, days: int = 7):
        """Export comprehensive report"""
        incidents = self.load_incidents(days=days)
        stats = self.get_statistics(days=days)
        
        report = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'period_days': days,
            'statistics': stats,
            'incidents': incidents
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return output_file
