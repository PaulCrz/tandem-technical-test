#!/usr/bin/env python3

"""
Tandem Technical Test - User Flow Analysis Script
Processes user events data to identify meaningful flows and anomalies.
"""

import json
import requests
from datetime import datetime
from collections import defaultdict, Counter
import statistics
from typing import Dict, List

class UserFlowAnalyzer:
    def __init__(self, data_url: str):
        self.data_url = data_url
        self.events = []
        self.user_sessions = defaultdict(lambda: defaultdict(list))
        self.flows = []
        self.anomalies = []

    def load_data(self) -> None:
        """Load JSON Lines data from URL."""
        print("Loading data from AWS...")
        response = requests.get(self.data_url)
        response.raise_for_status()

        valid_events = 0
        invalid_events = 0

        for line in response.text.strip().split('\n'):
            if line.strip():
                try:
                    event = json.loads(line)
                    # Validate required fields
                    if self._is_valid_event(event):
                        self.events.append(event)
                        valid_events += 1
                    else:
                        invalid_events += 1
                except json.JSONDecodeError:
                    invalid_events += 1

        print(f"Loaded {valid_events} valid events")
        if invalid_events > 0:
            print(f"Skipped {invalid_events} invalid events")

    def _is_valid_event(self, event: Dict) -> bool:
        """Validate that an event has required fields."""
        required_fields = ['user_id', 'session_id', 'event_time', 'path']

        for field in required_fields:
            if field not in event or event[field] is None:
                return False

        # Additional validation for event_time format
        try:
            datetime.fromisoformat(event['event_time'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return False

        return True

    def process_events(self) -> None:
        """Process events and group by user and session."""
        print("Processing events...")

        if not self.events:
            print("No valid events to process")
            return

        # Sort events by timestamp (now safe since we validated event_time)
        self.events.sort(key=lambda x: x['event_time'])

        # Group by user_id and session_id
        for event in self.events:
            user_id = event['user_id']
            session_id = event['session_id']
            self.user_sessions[user_id][session_id].append(event)

        print(f"Found {len(self.user_sessions)} unique users")
        total_sessions = sum(len(sessions) for sessions in self.user_sessions.values())
        print(f"Found {total_sessions} unique sessions")

    def analyze_flows(self) -> None:
        """Analyze user flows and identify meaningful patterns."""
        print("Analyzing user flows...")

        successful_checkouts = []
        abandoned_flows = []
        path_sequences = []

        for user_id, sessions in self.user_sessions.items():
            for session_id, events in sessions.items():
                # Extract path sequence for this session
                path_sequence = [event['path'] for event in events]
                path_sequences.append(path_sequence)

                # Check for successful checkout with improved detection
                if self._is_successful_checkout(events):
                    successful_checkouts.append({
                        'user_id': user_id,
                        'session_id': session_id,
                        'path_sequence': path_sequence,
                        'events': events
                    })
                else:
                    abandoned_flows.append({
                        'user_id': user_id,
                        'session_id': session_id,
                        'path_sequence': path_sequence,
                        'last_path': path_sequence[-1] if path_sequence else None,
                        'events': events
                    })

        # Analyze common flow patterns
        self._analyze_flow_patterns(successful_checkouts, abandoned_flows, path_sequences)

        # Add product insights
        self._analyze_product_insights()

        # Add page activity insights
        self._analyze_page_activity()

    def _is_successful_checkout(self, events: List[Dict]) -> bool:
        """Improved checkout detection with deduplication and content analysis."""
        checkout_events = []

        # Find all checkout events in the session
        for event in events:
            if event['path'] == '/checkout':
                checkout_events.append(event)

        if not checkout_events:
            return False

        # Check each checkout event for success indicators
        for checkout_event in checkout_events:
            css = checkout_event.get('css', '').lower()
            text = checkout_event.get('text', '').lower()

            # Check for failure indicators
            if 'error' in css or 'error' in text:
                continue
            if 'cancel' in css or 'cancel' in text:
                continue

            # Check for success indicator
            if 'place order' in text:
                return True

        return False

    def _analyze_product_insights(self) -> None:
        """Analyze most consulted products - count once per user session."""
        product_sessions = Counter()

        # Track unique product views per session
        for user_id, sessions in self.user_sessions.items():
            for session_id, events in sessions.items():
                # Get unique products viewed in this session
                products_in_session = set()
                for event in events:
                    path = event['path']
                    # Look for product pages that start with /products/
                    if path.startswith('/products/'):
                        products_in_session.add(path)

                # Count each unique product once per session
                for product in products_in_session:
                    product_sessions[product] += 1

        if product_sessions:
            # Calculate total sessions that viewed products
            total_product_sessions = sum(product_sessions.values())

            self.flows.append({
                'title': 'Most Consulted Products',
                'description': f'Analysis of products viewed across {total_product_sessions} user sessions',
                'details': {
                    'total_product_sessions': total_product_sessions,
                    'unique_products': len(product_sessions),
                    'top_products': product_sessions.most_common(10)
                }
            })

    def _analyze_page_activity(self) -> None:
        """Analyze pages with longest user activity."""
        page_durations = defaultdict(list)

        for user_id, sessions in self.user_sessions.items():
            for session_id, events in sessions.items():
                for i in range(len(events) - 1):
                    try:
                        current_time = datetime.fromisoformat(events[i]['event_time'].replace('Z', '+00:00'))
                        next_time = datetime.fromisoformat(events[i + 1]['event_time'].replace('Z', '+00:00'))
                        duration_seconds = (next_time - current_time).total_seconds()

                        # Only count reasonable durations (less than 30 minutes)
                        if 0 < duration_seconds < 1800:
                            page_durations[events[i]['path']].append(duration_seconds)
                    except (ValueError, AttributeError):
                        continue

        # Calculate average duration per page
        page_avg_durations = {}
        for path, durations in page_durations.items():
            if durations:
                page_avg_durations[path] = statistics.mean(durations)

        if page_avg_durations:
            # Sort by average duration
            sorted_pages = sorted(page_avg_durations.items(), key=lambda x: x[1], reverse=True)

            self.flows.append({
                'title': 'Pages with Longest Activity',
                'description': f'Analysis of user time spent on {len(sorted_pages)} different pages',
                'details': {
                    'total_pages_analyzed': len(sorted_pages),
                    'longest_activity_pages': [(path, f"{duration:.1f}s") for path, duration in sorted_pages[:10]],
                    'average_page_time': f"{statistics.mean(page_avg_durations.values()):.1f}s"
                }
            })

    def _analyze_flow_patterns(self, successful_checkouts: List[Dict],
                              abandoned_flows: List[Dict],
                              path_sequences: List[List[str]]) -> None:
        """Analyze and categorize flow patterns."""

        # Most common successful flow
        if successful_checkouts:
            successful_paths = [' → '.join(flow['path_sequence']) for flow in successful_checkouts]
            most_common_success = Counter(successful_paths).most_common(3)

            self.flows.append({
                'title': 'Successful Purchase Flows',
                'description': f'Found {len(successful_checkouts)} successful checkout sessions',
                'details': {
                    'total_successful': len(successful_checkouts),
                    'most_common_patterns': most_common_success,
                    'conversion_rate': f"{len(successful_checkouts) / len(path_sequences) * 100:.1f}%"
                }
            })

        # Abandonment analysis
        if abandoned_flows:
            abandonment_points = Counter([flow['last_path'] for flow in abandoned_flows if flow['last_path']])

            self.flows.append({
                'title': 'Flow Abandonment Patterns',
                'description': f'Analyzed {len(abandoned_flows)} abandoned sessions',
                'details': {
                    'total_abandoned': len(abandoned_flows),
                    'common_exit_points': abandonment_points.most_common(5),
                    'abandonment_rate': f"{len(abandoned_flows) / len(path_sequences) * 100:.1f}%"
                }
            })

        # Common entry points
        entry_points = Counter([seq[0] for seq in path_sequences if seq])
        self.flows.append({
            'title': 'User Entry Points',
            'description': 'Most common starting pages for user sessions',
            'details': {
                'top_entry_points': entry_points.most_common(5)
            }
        })

    def detect_anomalies(self) -> None:
        """Detect anomalies in user behavior and technical issues."""
        print("Detecting anomalies...")

        self._detect_time_gaps()
        self._detect_error_patterns()
        self._detect_unusual_behaviors()

    def _detect_time_gaps(self) -> None:
        """Detect unusually long gaps between events."""
        long_gaps = []

        for user_id, sessions in self.user_sessions.items():
            for session_id, events in sessions.items():
                if len(events) < 2:
                    continue

                for i in range(1, len(events)):
                    try:
                        prev_time = datetime.fromisoformat(events[i-1]['event_time'].replace('Z', '+00:00'))
                        curr_time = datetime.fromisoformat(events[i]['event_time'].replace('Z', '+00:00'))
                        gap_seconds = (curr_time - prev_time).total_seconds()

                        # Flag gaps longer than 5 minutes as potential user confusion
                        if gap_seconds > 300:
                            long_gaps.append({
                                'user_id': user_id,
                                'session_id': session_id,
                                'gap_minutes': gap_seconds / 60,
                                'stuck_on_page': events[i-1]['path'],
                                'next_page': events[i]['path']
                            })
                    except (ValueError, AttributeError) as e:
                        # Skip events with invalid timestamps
                        continue

        if long_gaps:
            # Group by page for better organization
            page_gaps = defaultdict(list)
            for gap in long_gaps:
                page_gaps[gap['stuck_on_page']].append(gap)

            # Sort by gap length
            long_gaps.sort(key=lambda x: x['gap_minutes'], reverse=True)

            self.anomalies.append({
                'title': 'User Confusion / Long Delays',
                'description': f'Found {len(long_gaps)} instances of users spending >5 minutes on a page',
                'severity': 'High' if len(long_gaps) > 10 else 'Medium',
                'details': {
                    'total_instances': len(long_gaps),
                    'average_gap': f"{statistics.mean([g['gap_minutes'] for g in long_gaps]):.1f} minutes",
                    'longest_gap': f"{max(long_gaps, key=lambda x: x['gap_minutes'])['gap_minutes']:.1f} minutes",
                    'page_specific_issues': page_gaps,
                    'examples': long_gaps[:3]
                }
            })

    def _detect_error_patterns(self) -> None:
        """Detect error-related patterns in CSS selectors and text."""
        error_events = []
        page_errors = defaultdict(list)

        for event in self.events:
            css = event.get('css', '').lower()
            text = event.get('text', '').lower()

            # Look for error-related keywords
            error_keywords = ['error', '404', 'timeout', 'failed', 'invalid', 'missing']

            if any(keyword in css or keyword in text for keyword in error_keywords):
                error_info = {
                    'event': event,
                    'error_type': 'CSS/Text contains error keywords',
                    'text': event.get('text', 'N/A'),
                    'css': event.get('css', 'N/A')
                }
                error_events.append(error_info)
                page_errors[event['path']].append(error_info)

        if error_events:
            self.anomalies.append({
                'title': 'Technical Errors',
                'description': f'Found {len(error_events)} events with error-related keywords',
                'severity': 'High',
                'details': {
                    'total_errors': len(error_events),
                    'page_specific_errors': page_errors
                }
            })

    def _detect_unusual_behaviors(self) -> None:
        """Detect unusual user behaviors."""
        # Detect sessions with unusually high event counts
        session_lengths = []
        for user_id, sessions in self.user_sessions.items():
            for session_id, events in sessions.items():
                session_lengths.append(len(events))

        if session_lengths:
            avg_length = statistics.mean(session_lengths)
            threshold = avg_length + 2 * statistics.stdev(session_lengths) if len(session_lengths) > 1 else avg_length * 2

            unusual_sessions = []
            for user_id, sessions in self.user_sessions.items():
                for session_id, events in sessions.items():
                    if len(events) > threshold:
                        unusual_sessions.append({
                            'user_id': user_id,
                            'session_id': session_id,
                            'event_count': len(events),
                            'duration_minutes': self._calculate_session_duration(events)
                        })

            if unusual_sessions:
                self.anomalies.append({
                    'title': 'Unusual Session Activity',
                    'description': f'Found {len(unusual_sessions)} sessions with unusually high activity',
                    'severity': 'Medium',
                    'details': {
                        'average_session_length': f"{avg_length:.1f} events",
                        'threshold': f"{threshold:.1f} events",
                        'unusual_sessions': unusual_sessions[:5]
                    }
                })

    def _calculate_session_duration(self, events: List[Dict]) -> float:
        """Calculate session duration in minutes."""
        if len(events) < 2:
            return 0

        try:
            start_time = datetime.fromisoformat(events[0]['event_time'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(events[-1]['event_time'].replace('Z', '+00:00'))
            return (end_time - start_time).total_seconds() / 60
        except (ValueError, AttributeError):
            return 0

    def generate_html_report(self) -> str:
        """Generate HTML report with findings."""
        print("Generating HTML report...")

        # Calculate average sessions per user
        total_sessions = sum(len(sessions) for sessions in self.user_sessions.values())
        avg_sessions_per_user = total_sessions / len(self.user_sessions) if self.user_sessions else 0

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User Flow Analysis Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .section {{
            background: white;
            margin: 20px 0;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .flow-item, .anomaly-item {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }}
        .anomaly-item {{
            border-left-color: #e74c3c;
        }}
        .anomaly-item.high {{
            border-left-color: #c0392b;
            background: #fdf2f2;
        }}
        .anomaly-item.medium {{
            border-left-color: #f39c12;
            background: #fef9e7;
        }}
        .flow-title, .anomaly-title {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
        }}
        .flow-description, .anomaly-description {{
            color: #7f8c8d;
            margin-bottom: 15px;
        }}
        .details {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
        }}
        .metric {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            margin: 5px;
            font-weight: bold;
        }}
        .metric.success {{ background: #27ae60; }}
        .metric.warning {{ background: #f39c12; }}
        .metric.danger {{ background: #e74c3c; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .summary-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}
        .summary-label {{
            color: #7f8c8d;
            font-size: 1.1em;
        }}
        .page-section {{
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 3px solid #667eea;
        }}
        .page-title {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        .timestamp {{
            color: #95a5a6;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>User Flow Analysis Report</h1>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="summary">
        <div class="summary-card">
            <div class="summary-number">{len(self.user_sessions)}</div>
            <div class="summary-label">Unique Users</div>
        </div>
        <div class="summary-card">
            <div class="summary-number">{total_sessions}</div>
            <div class="summary-label">Total Sessions</div>
        </div>
        <div class="summary-card">
            <div class="summary-number">{avg_sessions_per_user:.1f}</div>
            <div class="summary-label">Avg Sessions/User</div>
        </div>
        <div class="summary-card">
            <div class="summary-number">{len(self.events)}</div>
            <div class="summary-label">Total Events</div>
        </div>
        <div class="summary-card">
            <div class="summary-number">{len(self.anomalies)}</div>
            <div class="summary-label">Anomalies Detected</div>
        </div>
    </div>

    <div class="section">
        <h2>📊 Meaningful User Flows</h2>
        {self._generate_flows_html()}
    </div>

    <div class="section">
        <h2>🚨 Detected Anomalies</h2>
        {self._generate_anomalies_html()}
    </div>
</body>
</html>
        """

        return html

    def _generate_flows_html(self) -> str:
        """Generate HTML for user flows section."""
        if not self.flows:
            return "<p>No significant flows detected.</p>"

        html = ""
        for flow in self.flows:
            html += f"""
            <div class="flow-item">
                <div class="flow-title">{flow['title']}</div>
                <div class="flow-description">{flow['description']}</div>
                <div class="details">
                    {self._format_flow_details(flow['details'])}
                </div>
            </div>
            """

        return html

    def _format_flow_details(self, details: Dict) -> str:
            """Format flow details as HTML."""
            html = ""

            for key, value in details.items():
                if key == 'most_common_patterns' and isinstance(value, list):
                    html += f"<strong>{key.replace('_', ' ').title()}:</strong>"
                    html += "<div style='margin: 15px 0;'>"
                    for pattern, count in value:
                        # Split the pattern by the arrow separator
                        paths = pattern.split(' → ')
                        html += "<div style='margin: 10px 0; padding: 12px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #27ae60;'>"
                        html += "<div style='display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-bottom: 8px;'>"

                        for i, path in enumerate(paths):
                            # Add chip for each path
                            html += f"<span style='background: #667eea; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85em; font-weight: 500;'>{path}</span>"

                            # Add arrow between paths (except for the last one)
                            if i < len(paths) - 1:
                                html += "<span style='color: #7f8c8d; font-weight: bold; margin: 0 4px;'>→</span>"

                        html += "</div>"
                        html += f"<div style='text-align: right;'><span class='metric success'>{count} completions</span></div>"
                        html += "</div>"
                    html += "</div>"
                elif key == 'common_exit_points' and isinstance(value, list):
                    html += f"<strong>{key.replace('_', ' ').title()}:</strong><ul>"
                    for page, count in value:
                        html += f"<li>{page} <span class='metric warning'>{count} exits</span></li>"
                    html += "</ul>"
                elif key == 'top_entry_points' and isinstance(value, list):
                    html += f"<strong>{key.replace('_', ' ').title()}:</strong><ul>"
                    for page, count in value:
                        html += f"<li>{page} <span class='metric success'>{count} entries</span></li>"
                    html += "</ul>"
                elif key == 'top_products' and isinstance(value, list):
                    html += f"<strong>{key.replace('_', ' ').title()}:</strong><ul>"
                    for product, count in value:
                        html += f"<li>{product} <span class='metric success'>{count} views</span></li>"
                    html += "</ul>"
                elif key == 'longest_activity_pages' and isinstance(value, list):
                    html += f"<strong>{key.replace('_', ' ').title()}:</strong><ul>"
                    for page, duration in value:
                        html += f"<li>{page} <span class='metric warning'>{duration}</span></li>"
                    html += "</ul>"
                else:
                    metric_class = ""
                    if 'conversion' in key:
                        metric_class = "success"
                    elif 'abandonment' in key:
                        metric_class = "warning"

                    html += f"<span class='metric {metric_class}'>{key.replace('_', ' ').title()}: {value}</span>"

            return html

    def _generate_anomalies_html(self) -> str:
        """Generate HTML for anomalies section."""
        if not self.anomalies:
            return "<p>No anomalies detected.</p>"

        html = ""
        for anomaly in self.anomalies:
            severity_class = anomaly.get('severity', 'medium').lower()
            html += f"""
            <div class="anomaly-item {severity_class}">
                <div class="anomaly-title">{anomaly['title']}</div>
                <div class="anomaly-description">{anomaly['description']}</div>
                <div class="details">
                    {self._format_anomaly_details(anomaly['details'])}
                </div>
            </div>
            """

        return html

    def _format_anomaly_details(self, details: Dict) -> str:
        """Format anomaly details as HTML."""
        html = ""

        for key, value in details.items():
            if key == 'page_specific_issues' and isinstance(value, dict):
                html += f"<strong>Issues by Page:</strong>"
                for page, issues in value.items():
                    html += f"""
                    <div class="page-section">
                        <div class="page-title">{page} ({len(issues)} issues)</div>
                        <ul>
                    """
                    # Show most common example for this page
                    if issues:
                        example = max(issues, key=lambda x: x.get('gap_minutes', 0))
                        if 'gap_minutes' in example:
                            html += f"<li>Longest delay: {example['gap_minutes']:.1f} minutes</li>"
                    html += "</ul></div>"
            elif key == 'page_specific_errors' and isinstance(value, dict):
                html += f"<strong>Errors by Page:</strong>"
                for page, errors in value.items():
                    # Count error texts for this page
                    error_texts = [e['text'] for e in errors if e['text'] != 'N/A']
                    error_text_counts = Counter(error_texts)

                    html += f"""
                    <div class="page-section">
                        <div class="page-title">{page} ({len(errors)} errors)</div>
                        <ul>
                    """
                    # Show most common error texts for this page
                    if error_text_counts:
                        for error_text, count in error_text_counts.most_common(3):
                            html += f"<li>'{error_text}': {count} occurrences</li>"
                    else:
                        html += f"<li>CSS-only errors: {len(errors)} occurrences</li>"
                    html += "</ul></div>"
            elif key == 'examples' and isinstance(value, list):
                html += f"<strong>{key.replace('_', ' ').title()}:</strong><ul>"
                for example in value[:3]:  # Limit to 3 examples
                    if isinstance(example, dict):
                        if 'gap_minutes' in example:
                            html += f"<li>User stuck on {example['stuck_on_page']} for {example['gap_minutes']:.1f} minutes</li>"
                        elif 'event_count' in example:
                            html += f"<li>Session with {example['event_count']} events ({example['duration_minutes']:.1f} minutes)</li>"
                html += "</ul>"
            elif key == 'most_problematic_pages' and isinstance(value, list):
                html += f"<strong>{key.replace('_', ' ').title()}:</strong><ul>"
                for page, count in value:
                    html += f"<li>{page} <span class='metric danger'>{count} issues</span></li>"
                html += "</ul>"
            elif key == 'error_pages' and isinstance(value, list):
                # This section is now handled by page_specific_errors
                pass
            elif not isinstance(value, (list, dict)):
                html += f"<span class='metric'>{key.replace('_', ' ').title()}: {value}</span>"

        return html

    def run_analysis(self) -> str:
        """Run complete analysis and return HTML report."""
        self.load_data()
        self.process_events()
        self.analyze_flows()
        self.detect_anomalies()
        return self.generate_html_report()

def main():
    """Main function to run the analysis."""
    data_url = "https://s3.eu-central-1.amazonaws.com/public.prod.usetandem.ai/sessions.json"

    analyzer = UserFlowAnalyzer(data_url)
    html_report = analyzer.run_analysis()

    # Save report to file
    with open('user_flow_report.html', 'w', encoding='utf-8') as f:
        f.write(html_report)

    print("Analysis complete! Report saved to 'user_flow_report.html'")
    print(f"Found {len(analyzer.flows)} meaningful flows and {len(analyzer.anomalies)} anomalies")

if __name__ == "__main__":
    main()
