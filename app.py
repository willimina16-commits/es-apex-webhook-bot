from flask import Flask, request
from datetime import datetime, timedelta

app = Flask(__name__)

# =========================
# APEX ES SAFE SETTINGS
# =========================
START_BALANCE = 50000
TRAILING_DRAWDOWN = 2500
MAX_TRADES_PER_DAY = 3
COOLDOWN_MINUTES = 30

# =========================
# STATE
# =========================
equity = START_BALANCE
peak_equity = START_BALANCE
trade_count = 0
position_open = False
last_loss_time = None
current_day = datetime.now().date()


# =========================
# RESET DAILY STATE
# =========================
def reset_day():
    global trade_count, current_day, position_open

    if datetime.now().date() != current_day:
        trade_count = 0
        position_open = False
        current_day = datetime.now().date()


# =========================
# DRAWDOWN CHECK
# =========================
def get_drawdown():
    global peak_equity

    if equity > peak_equity:
        peak_equity = equity

    return peak_equity - equity


# =========================
# COOLDOWN CHECK
# =========================
def in_cooldown():
    global last_loss_time

    if not last_loss_time:
        return False

    return datetime.now() < last_loss_time + timedelta(minutes=COOLDOWN_MINUTES)


# =========================
# RISK ENGINE
# =========================
def can_trade():
    if trade_count >= MAX_TRADES_PER_DAY:
        return False, "Max trades reached"

    if get_drawdown() >= TRAILING_DRAWDOWN:
        return False, "Trailing drawdown hit"

    if position_open:
        return False, "Position already open"

    if in_cooldown():
        return False, "Cooldown active"

    return True, "OK"


# =========================
# EXECUTION (PLACEHOLDER)
# =========================
def place_order(side):
    print(f"EXECUTING {side.upper()} ES ORDER")
    # Later: connect Tradovate API here
    return True


# =========================
# WEBHOOK ENDPOINT
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():
    global trade_count, position_open

    reset_day()

    data = request.json
    side = data.get("side")

    allowed, reason = can_trade()

    if not allowed:
        return {"status": "blocked", "reason": reason}

    if side not in ["buy", "sell"]:
        return {"status": "ignored"}

    place_order(side)

    trade_count += 1
    position_open = True

    return {
        "status": "executed",
        "side": side,
        "trades_today": trade_count
    }


# =========================
# CLOSE POSITION (manual)
# =========================
@app.route("/close", methods=["POST"])
def close():
    global position_open
    position_open = False
    return {"status": "closed"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
