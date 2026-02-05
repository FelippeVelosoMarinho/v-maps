# v-maps
aaaaaa


### Rodar a API
```
# ative o virtualenv
source .venv/bin/activate

# instale as dependências
pip install -r requirements.txt

cd api
python -m uvicorn app.main:app --reload --port 8000
```

### Rodar o client
```
cd client
pnpm run dev
```

### Rodar no Android (via Capacitor)
Para testar via Android Studio:
```bash
cd client
pnpm run build
npx cap sync
npx cap open android
```
No Android Studio, aguarde o sync do Gradle e clique em **Run**.