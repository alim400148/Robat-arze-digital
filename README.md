# Robat-arze-digital
ربات سیگنال تلگرام حد سود و ضرر
# bot.py
import time
import logging
import pandas as pd
import json
import os
from datetime import datetime
from binance.client import Client
import ta
import mplfinance as mpf
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# -----------------------------
# 🔐 تنظیمات (حتماً ویرایش کن)
# -----------------------------
TELEGRAM_TOKEN = 'YOUR_TELEGRAM_TOKEN_HERE'  # ← توکن رباتت
YOUR_USER_ID = 123456789  # ← یوزرآی‌دی عددی خودت
API_KEY_BINANCE = ''
API_SECRET_BINANCE = ''

# اتصال به Binance Testnet
client = Client(API_KEY_BINANCE, API_SECRET_BINANCE, testnet=True)

# فعال‌سازی گزارش خطا
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# -----------------------------
# 📥 دریافت داده
# -----------------------------
def get_klines(symbol, interval='5m', limit=100):
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            'Time', 'Open', 'High', 'Low', 'Close', 'Volume',
            'CloseTime', 'QuoteVolume', 'Trades', 'TakerBuyBase', 'TakerBuyQuote', 'Ignore'
        ])
        df['Close'] = pd.to_numeric(df['Close'])
        df['Open'] = pd.to_numeric(df['Open'])
        df['High'] = pd.to_numeric(df['High'])
        df['Low'] = pd.to_numeric(df['Low'])
        df['Volume'] = pd.to_numeric(df['Volume'])
        df['Time'] = pd.to_datetime(df['Time'], unit='ms')
        return df
    except Exception as e:
        print(f"❌ خطا: {e}")
        return pd.DataFrame()

# -----------------------------
# 📊 اندیکاتورها
# -----------------------------
def add_indicators(df):
    df['EMA9'] = ta.trend.EMAIndicator(df['Close'], window=9).ema_indicator()
    df['EMA21'] = ta.trend.EMAIndicator(df['Close'], window=21).ema_indicator()
    df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    df['Volume_MA'] = df['Volume'].rolling(20).mean()
    return df.dropna()

# -----------------------------
# 🧠 تولید سیگنال
# -----------------------------
def generate_signal(df, symbol):
    if len(df) < 50:
        return None, None
    current = df.iloc[-1]
    prev = df.iloc[-2]

    # شرط خرید
    if (prev['EMA9'] <= prev['EMA21'] and current['EMA9'] > current['EMA21'] and
        prev['RSI'] < 30 and current['RSI'] > 30 and
        current['Volume'] > current['Volume_MA'] * 0.8):

        entry = current['Close']
        stop_loss = current['Low'] * 0.995
        tp1 = entry + 1.5 * (entry - stop_loss)
        tp2 = entry + 3 * (entry - stop_loss)

        return "🟢 خرید", {
            'entry': round(entry, 4),
            'stop_loss': round(stop_loss, 4),
            'tp1': round(tp1, 4),
            'tp2': round(tp2, 4),
            'rsi': round(current['RSI'], 2)
        }

    # شرط فروش
    elif (prev['EMA9'] >= prev['EMA21'] and current['EMA9'] < current['EMA21'] and
          prev['RSI'] > 70 and current['RSI'] < 70 and
          current['Volume'] > current['Volume_MA'] * 0.8):

        entry = current['Close']
        stop_loss = current['High'] * 1.005
        tp1 = entry - 1.5 * (stop_loss - entry)
        tp2 = entry - 3 * (stop_loss - entry)

        return "🔴 فروش", {
            'entry': round(entry, 4),
            'stop_loss': round(stop_loss, 4),
            'tp1': round(tp1, 4),
            'tp2': round(tp2, 4),
            'rsi': round(current['RSI'], 2)
        }

    return None, None

# -----------------------------
# 📈 رسم نمودار
# -----------------------------
def plot_candlestick(df, symbol, signal_type, save_path="signal_chart.png"):
    try:
        data = df[-50:].copy()
        data.set_index('Time', inplace=True)
        data['EMA9'] = ta.trend.EMAIndicator(data['Close'], window=9).ema_indicator()
        data['EMA21'] = ta.trend.EMAIndicator(data['Close'], window=21).ema_indicator()

        ap = [
            mpf.make_addplot(data['EMA9'], color='blue'),
            mpf.make_addplot(data['EMA21'], color='orange')
        ]

        if signal_type == "BUY":
            ap.append(mpf.make_addplot([data['Low'].iloc[-1]], type='scatter', markersize=200, marker='^', color='green'))
            title = f"{symbol} - سیگنال خرید"
        elif signal_type == "SELL":
            ap.append(mpf.make_addplot([data['High'].iloc[-1]], type='scatter', markersize=200, marker='v', color='red'))
            title = f"{symbol} - سیگنال فروش"

        fig, axlist = mpf.plot(data, type='candle', addplot=ap, title=title, style='yahoo', returnfig=True)
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        return save_path
    except Exception as e:
        print(f"❌ خطا: {e}")
        return None

# -----------------------------
# 📁 ذخیره سیگنال
# -----------------------------
def log_signal(symbol, signal, details):
    with open("signals.json", "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "time": datetime.now().isoformat(),
            "symbol": symbol,
            "signal": signal,
            "details": details
        }, ensure_ascii=False) + "\n")

# -----------------------------
# 📣 دستورات تلگرام
# -----------------------------
def start(update: Update, context: CallbackContext):
    if update.message.from_user.id != YOUR_USER_ID:
        update.message.reply_text("❌ دسترسی محدود.")
        return
    update.message.reply_text(
        "🤖 ربات سیگنال حرفه‌ای آماده است!\n"
        "دستورات:\n"
        "/signal - سیگنال فوری\n"
        "/set 300 - هر ۵ دقیقه چک کن\n"
        "/unset - توقف"
    )

def send_signal(update: Update, context: CallbackContext):
    if update.message.from_user.id != YOUR_USER_ID:
        return
    symbols = ['BTCUSDT', 'ETHUSDT']
    found = False
    for symbol in symbols:
        df = get_klines(symbol, '5m')
        if df.empty or len(df) < 50: continue
        df = add_indicators(df)
        signal, details = generate_signal(df, symbol)
        if signal:
            msg = (f"🚀 {symbol}\n{signal}\n📍 ورود: {details['entry']}\n"
                   f"🔻 حد ضرر: {details['stop_loss']}\n"
                   f"🔺 TP1: {details['tp1']} | TP2: {details['tp2']}\n"
                   f"📊 RSI: {details['rsi']}")
            update.message.reply_text(msg)
            chart = plot_candlestick(df, symbol, "BUY" if "خرید" in signal else "SELL")
            if chart and os.path.exists(chart):
                update.message.reply_photo(photo=open(chart, 'rb'))
                os.remove(chart)
            log_signal(symbol, signal, details)
            found = True
    if not found:
        update.message.reply_text("❌ سیگنالی یافت نشد.")

def set_timer(update: Update, context: CallbackContext):
    try:
        interval = int(context.args[0])
        context.job_queue.stop()
        context.job_queue.run_repeating(lambda ctx: send_signal(update, context), interval=interval, first=1)
        update.message.reply_text(f"✅ هر {interval} ثانیه چک می‌شه.")
    except:
        update.message.reply_text("❌ مقدار نامعتبر.")

def unset(update: Update, context: CallbackContext):
    context.job_queue.stop()
    update.message.reply_text("🛑 توقف شد.")

# -----------------------------
# 🚀 اجرا
# -----------------------------
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("signal", send_signal))
    dp.add_handler(CommandHandler("set", set_timer))
    dp.add_handler(CommandHandler("unset", unset))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
    # 🚀 ربات سیگنال تلگرامی

ربات هوشمند برای تشخیص سیگنال خرید/فروش با رعایت مدیریت ریسک، حد ضرر و حد سود.

## 🔧 نصب
```bash
pip install -r requirements.txt
python-3.10.12
python-telegram-bot==13.15
python-binance
pandas
ta
mplfinance
numpy
<!DOCTYPE html>
<html lang="fa">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>🚀 داشبورد سیگنال</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    body { font-family: Tahoma; text-align: center; padding: 20px; direction: rtl; }
    .signal { border: 1px solid #ddd; margin: 10px; padding: 10px; border-radius: 8px; }
    .buy { border-right: 5px solid green; }
    .sell { border-right: 5px solid red; }
  </style>
</head>
<body>
  <h1>🚀 داشبورد سیگنال</h1>
  <div id="signals">در حال بارگذاری...</div>
  <script>
    fetch('https://your-username.github.io/crypto-signal-bot/signals.json')
      .then(r => r.json())
      .then(data => {
        const signals = Array.isArray(data) ? data.reverse() : [data];
        document.getElementById('signals').innerHTML = signals.map(s => 
          `<div class="signal ${s.signal.includes('خرید')?'buy':'sell'}">
            <h3>${s.signal}</h3>
            <p>جفت: ${s.symbol}</p>
            <p>ورود: ${s.details.entry}</p>
            <p>حد ضرر: ${s.details.stop_loss}</p>
            <p>حد سود: ${s.details.tp1}, ${s.details.tp2}</p>
            <p>زمان: ${new Date(s.time).toLocaleTimeString('fa-IR')}</p>
          </div>`
        ).join('');
      })
      .catch(() => document.getElementById('signals').textContent = "خطا در بارگذاری");
  </script>
</body>
</html>

---

## ✅ فایل ۵: `.gitignore`

```txt
__pycache__/
*.pyc
.DS_Store
.env
signals.json
signal_chart.png
python bot.py
