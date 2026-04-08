# Connecting to Your Local Interactive Brokers Gateway

To run this bot against your real or paper trading account from your local machine, follow these steps:

## 1. Install & Configure IB Gateway or TWS
1. Download and install **IB Gateway** (recommended for bots) or **Trader Workstation (TWS)** from the Interactive Brokers website.
2. Log in with your Paper Trading or Live account.
3. Enable API access:
   - **IB Gateway**: `Settings` -> `API` -> `Settings`.
   - **TWS**: `Edit` -> `Global Configuration` -> `API` -> `Settings`.
4. Check **"Enable ActiveX and Socket Clients"**.
5. Set the **"Socket Port"**:
   - Paper Trading: Typically `7497`
   - Live Trading: Typically `7496`
6. Note down your **"Trusted IPs"** or add `127.0.0.1` to the list.
7. Uncheck **"Read-Only API"** if you want the bot to place trades.

## 2. Update Environment Variables
In your `.env` file, ensure the following variables match your IB setup:
```env
IB_HOST=127.0.0.1
IB_PORT=7497  # Use 7496 for live
IB_CLIENT_ID=1 # Any unique integer
IB_ACCOUNT=DU123456 # Your IB account ID (starts with U or DU)
```

## 3. Run the Bot in Docker
If you are running the bot inside Docker but IB Gateway is on your host machine (MacBook), use `host.docker.internal` instead of `127.0.0.1`:
```env
IB_HOST=host.docker.internal
```

## 4. Verify Connection
Run the following command to test the real connection (this will bypass the mock if the host is not `127.0.0.1` or if you've updated the `seed_brokers` host):
```bash
python backend/manage.py run_verification
```

---
**Note for Nigeria-based users:**
Interactive Brokers is generally available in Nigeria. Ensure you have a stable internet connection as the bot requires a persistent socket connection to the IB Gateway to receive market data and status updates.
