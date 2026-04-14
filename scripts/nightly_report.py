import os
import json
from datetime import datetime

def load_sessions(sessions_dir):
    sessions = []
    for entry in os.listdir(sessions_dir):
        session_path = os.path.join(sessions_dir, entry)
        if os.path.isdir(session_path) and os.path.exists(os.path.join(session_path, 'session.json')):
            with open(os.path.join(session_path, 'session.json'), 'r') as file:
                sessions.append((entry, json.load(file)))
    return sessions

def generate_report(sessions):
    report = []
    
    # Report timestamp
    report.append("# Nightly Report\n")
    report.append(f"Generated on: {datetime.now()}\n\n")
    
    # Totals section
    total_sessions = len(sessions)
    reviewed_sessions_count = sum(1 for session in sessions if session[1]['verdict'])
    unreviewed_sessions_count = total_sessions - reviewed_sessions_count
    accepted_count = sum(1 for session in sessions if session[1]['verdict'] == 'accepted')
    accepted_with_edits_count = sum(1 for session in sessions if session[1]['verdict'] == 'accepted_with_edits')
    rejected_count = sum(1 for session in sessions if session[1]['verdict'] == 'rejected')
    
    report.append("## Totals\n")
    report.append(f"- Total Sessions: {total_sessions}\n")
    report.append(f"- Reviewed Sessions: {reviewed_sessions_count}\n")
    report.append(f"- Unreviewed Sessions: {unreviewed_sessions_count}\n")
    report.append(f"- Accepted: {accepted_count}\n")
    report.append(f"- Accepted with Edits: {accepted_with_edits_count}\n")
    report.append(f"- Rejected: {rejected_count}\n\n")
    
    # Average score
    scores = [session[1]['score'] for session in sessions if session[1]['score']]
    average_score = sum(scores) / len(scores) if scores else None
    
    report.append("## Average Score\n")
    report.append(f"- Average Score: {average_score:.2f}" if average_score is not None else "- Average Score: N/A\n\n")
    
    # Top failure tags
    failure_tags = [tag for session in sessions for tag in session[1]['failure_tags']]
    failure_tag_counts = {}
    for tag in failure_tags:
        if tag in failure_tag_counts:
            failure_tag_counts[tag] += 1
        else:
            failure_tag_counts[tag] = 1
    
    top_failure_tags = sorted(failure_tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    report.append("## Top Failure Tags\n")
    if not top_failure_tags:
        report.append("- No failure tags recorded.\n")
    else:
        for tag, count in top_failure_tags:
            report.append(f"- {tag}: {count}\n")
    
    # Per-session summary table
    report.append("\n## Per-Session Summary\n")
    report.append("| Session ID | Task Title | Task Type | Verdict | Score | Notes Summary |\n")
    report.append("|------------|------------|-----------|---------|-------|---------------|\n")
    for session_id, session_data in sorted(sessions, key=lambda x: x[0], reverse=True):
        verdict = session_data.get('verdict', 'unreviewed')
        score = session_data.get('score', None)
        notes_summary = session_data.get('notes_summary', '')
        
        report.append(f"| {session_id} | {session_data['task_title']} | {session_data['task_type']} | {verdict} | {score if score is not None else 'N/A'} | {notes_summary if notes_summary else 'N/A'} |\n")
    
    return '\n'.join(report)

def main():
    sessions_dir = 'sessions'
    reports_dir = 'reports'
    
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    
    sessions = load_sessions(sessions_dir)
    report_content = generate_report(sessions)
    
    with open(os.path.join(reports_dir, 'nightly_report.md'), 'w') as file:
        file.write(report_content)

if __name__ == "__main__":
    main()
