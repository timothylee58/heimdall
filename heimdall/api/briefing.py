def briefing(ledger):
    report = ledger.read()
    lines = ['Heimdall local owner briefing', f"Audit valid: {report['verification']['valid']}", 'All execution and notifications are simulated.']
    for entry in report['events']:
        event = entry['event']
        if event.get('type') == 'state':
            continue
        result = event['result']
        lines.append(f"{entry['seq']}. {result['key']}: {result['tier']} / {result['status']}")
        if event['type'] == 'approval':
            lines.append('Owner note: ' + event['decision']['owner_note'])
        if 'notification' in result:
            lines.append(result['notification'])
    return '\n'.join(lines) + '\n'
