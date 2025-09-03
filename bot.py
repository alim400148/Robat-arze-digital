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

if name == "__main__":
    main()
python-telegram-bot==13.15
python-binance
pandas
ta
mplfinance
numpy

python-3.10.12

# 🚀 ربات سیگنال تلگرامی

ربات هوشمند برای تشخیص سیگنال خرید/فروش با رعایت مدیریت ریسک، حد ضرر و حد سود.

## 🔧 نصب
`bash
pip install -r requirements.txt

# 🚀 ربات سیگنال تلگرامی

ربات هوشمند برای تشخیص سیگنال خرید/فروش با رعایت مدیریت ریسک، حد ضرر و حد سود.

## 🔧 نصب
`bash
pip install -r requirements.txt

python bot.py

---

## ✅ فایل ۵: .gitignore

`txt
pycache/
*.pyc
.DS_Store
.env
signals.json
signal_chart.png

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
          <div class="signal ${s.signal.includes('خرید')?'buy':'sell'}">
            <h3>${s.signal}</h3>
            <p>جفت: ${s.symbol}</p>
            <p>ورود: ${s.details.entry}</p>
            <p>حد ضرر: ${s.details.stop_loss}</p>
            <p>حد سود: ${s.details.tp1}, ${s.details.tp2}</p>
            <p>زمان: ${new Date(s.time).toLocaleTimeString('fa-IR')}</p>
          </div>
        ).join('');
      })
      .catch(() => document.getElementById('signals').textContent = "خطا در بارگذاری");
  </script>
</body>
</html>


