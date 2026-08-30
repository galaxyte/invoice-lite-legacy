# Legacy reporting module -- kept for reference from the old system.
# Not imported by app.py; nobody has gotten around to porting it to Python 3.


def generate_legacy_summary(invoices):
    print "Generating legacy summary..."
    total = 0
    for inv in invoices:
        total += inv['amount']
    print "Total: %s" % total
    return total
