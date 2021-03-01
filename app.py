from flask import Flask, jsonify, request

app = Flask(__name__)

INVOICES = []


@app.route("/invoices", methods=["GET"])
def list_invoices():
    return jsonify(INVOICES)


@app.route("/invoices", methods=["POST"])
def create_invoice():
    data = request.get_json()
    invoice = {"id": len(INVOICES) + 1, "client": data["client"], "amount": data["amount"]}
    INVOICES.append(invoice)
    return jsonify(invoice), 201


@app.route("/invoices/<int:invoice_id>", methods=["GET"])
def get_invoice(invoice_id):
    for inv in INVOICES:
        if inv["id"] == invoice_id:
            return jsonify(inv)
    return jsonify({"error": "not found"}), 404


def calculate_total(invoices):
    return sum(inv["amount"] for inv in invoices)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
