import csv
from datetime import datetime
from statistics import mean
from colorama import Fore, Style, init
import platform
import matplotlib.pyplot as plt

# Firebase
import firebase_admin
from firebase_admin import credentials, firestore

# ==========================
# Inicialização Firebase
# ==========================
cred = credentials.Certificate("serviceAccountKey.json")  # seu arquivo JSON
firebase_admin.initialize_app(cred)
db = firestore.client()

# ==========================
# Variáveis globais
# ==========================
ultimo_call = None
historico_acertos = {"acertos": 0, "erros": 0}
historico_por_faixa = {"2x": {"acertos": 0, "erros": 0},
                       "5x": {"acertos": 0, "erros": 0},
                       "10x": {"acertos": 0, "erros": 0}}

# ==========================
# Funções auxiliares
# ==========================
if platform.system() == "Windows":
    import winsound

init(autoreset=True)

def beep():
    try:
        if platform.system() == "Windows":
            winsound.Beep(1200, 300)
        print("\a", end="")
    except:
        pass

def faixa_resultado(r):
    if r < 2:
        return "<2x"
    elif r < 5:
        return "2–5x"
    elif r < 10:
        return "5–10x"
    elif r < 20:
        return "10–20x"
    else:
        return "20+"

def enviar_call_firebase(call, confianca, modo):
    """Envia a call para o Firestore"""
    try:
        doc_ref = db.collection("calls").document()
        doc_ref.set({
            "call": call,
            "confianca": confianca,
            "modo": modo,
            "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Aberta"
        })
        print(f"📡 Call enviada para Firebase: {call} ({confianca}%)")
    except Exception as e:
        print(f"❌ Erro ao enviar call para Firebase: {e}")

# ==========================
# Análise Inteligente
# ==========================
def analisar_inteligente(resultados):
    global ultimo_call

    total = len(resultados)
    if total < 3:
        return None

    prob_15x = sum(1 for r in resultados if r >= 1.5) / total * 100
    prob_2x = sum(1 for r in resultados if r >= 2) / total * 100
    prob_5x = sum(1 for r in resultados if r >= 5) / total * 100
    prob_10x = sum(1 for r in resultados if r >= 10) / total * 100

    ultimos3 = resultados[-3:]
    ultimos10 = resultados[-10:]
    ultimos20 = resultados[-20:] if total >= 20 else resultados

    prob_ponderada = (
        (sum(1 for r in ultimos3 if r >= 2) / len(ultimos3) * 100) * 0.5 +
        (sum(1 for r in ultimos10 if r >= 2) / len(ultimos10) * 100) * 0.3 +
        (sum(1 for r in ultimos20 if r >= 2) / len(ultimos20) * 100) * 0.2
    )

    media_20 = round(mean(ultimos20), 2)

    sequencia_baixa = 0
    for r in reversed(resultados):
        if r < 2:
            sequencia_baixa += 1
        else:
            break

    freq = {"<2x": 0, "2–5x": 0, "5–10x": 0, "10–20x": 0, "20+": 0}
    for r in ultimos10:
        freq[faixa_resultado(r)] += 1

    spike20 = any(r >= 20 for r in ultimos10)
    spike40 = any(r >= 40 for r in ultimos10)

    calls = []
    modo = "Neutro"

    if sequencia_baixa >= 3:
        calls.append(("⚡ Sequência baixa detectada — boa chance até 2x", 75))
        modo = "Conservador"

    if prob_2x >= 55 or prob_15x >= 75:
        if freq["<2x"] < 6:
            calls.append(("✅ Entrada segura até 2x", max(prob_2x, prob_15x)))
            modo = "Conservador"

    if prob_5x >= 25 and sequencia_baixa == 0:
        if freq["2–5x"] < 6:
            calls.append(("⚠️ Entrada moderada até 5x", prob_5x))
            modo = "Moderado"

    if prob_10x >= 10 and freq["5–10x"] < 4:
        calls.append(("🔥 Entrada agressiva até 10x", prob_10x))
        modo = "Agressivo"

    if spike40:
        calls.append(("🚫 Spike >40x detectado — evitar entradas longas agora", 90))
    elif spike20:
        calls.append(("🚫 Spike >20x detectado — tendência de fase baixa", 85))

    if not calls:
        calls.append(("❌ Melhor esperar — cenário neutro", 100))

    ultimo_call = max(calls, key=lambda x: x[1])

    # Enviar para Firebase
    enviar_call_firebase(ultimo_call[0], ultimo_call[1], modo)

    return {
        "prob_15x": round(prob_15x, 2),
        "prob_2x": round(prob_2x, 2),
        "prob_5x": round(prob_5x, 2),
        "prob_10x": round(prob_10x, 2),
        "prob_ponderada": round(prob_ponderada, 2),
        "media_20": media_20,
        "sequencia_baixa": sequencia_baixa,
        "ultimos10": ultimos10,
        "modo": modo,
        "freq": freq,
        "calls": calls
    }

# ==========================
# Avaliar Calls
# ==========================
def avaliar_call(resultado_real):
    global ultimo_call, historico_acertos, historico_por_faixa

    if ultimo_call:
        limite = 2 if "2x" in ultimo_call[0] else 5 if "5x" in ultimo_call[0] else 10
        faixa = "2x" if limite == 2 else "5x" if limite == 5 else "10x"

        if "❌ Melhor esperar" in ultimo_call[0] or "🚫" in ultimo_call[0]:
            print("👉 Última call foi de esperar — não conta acerto/erro.")
            return

        if resultado_real >= limite:
            historico_acertos["acertos"] += 1
            historico_por_faixa[faixa]["acertos"] += 1
            print("👉 Resultado da última call: ACERTOU ✅")
        else:
            historico_acertos["erros"] += 1
            historico_por_faixa[faixa]["erros"] += 1
            print("👉 Resultado da última call: ERROU ❌")

        total = historico_acertos["acertos"] + historico_acertos["erros"]
        taxa = historico_acertos["acertos"] / total * 100 if total > 0 else 0
        print(f"Taxa global: {taxa:.2f}% "
              f"({historico_acertos['acertos']} acertos / {historico_acertos['erros']} erros)")

        if historico_por_faixa[faixa]["acertos"] + historico_por_faixa[faixa]["erros"] > 0:
            taxa_faixa = historico_por_faixa[faixa]["acertos"] / (
                historico_por_faixa[faixa]["acertos"] + historico_por_faixa[faixa]["erros"]
            ) * 100
            print(f"Taxa de acerto para calls {faixa}: {taxa_faixa:.2f}%")

# ==========================
# CSV e Gráficos
# ==========================
def salvar_csv(analise):
    with open("historico_aviator.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow([
                "DataHora", "Prob>1.5x", "Prob>2x", "Prob>5x", "Prob>10x",
                "Prob Ponderada", "Media_20", "Sequencia_Baixa",
                "Ultimos10", "Frequencias", "Modo", "Calls"
            ])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            analise["prob_15x"], analise["prob_2x"], analise["prob_5x"], analise["prob_10x"],
            analise["prob_ponderada"], analise["media_20"], analise["sequencia_baixa"],
            analise["ultimos10"], analise["freq"], analise["modo"],
            [(c[0], f"{c[1]}%") for c in analise["calls"]]
        ])

def plotar_grafico(resultados, analise):
    ultimos20 = resultados[-20:] if len(resultados) >= 20 else resultados
    plt.figure(figsize=(10, 5))
    plt.plot(ultimos20, marker="o", color="blue", label="Resultados")

    for i, r in enumerate(ultimos20):
        if r < 1.5:
            plt.plot(i, r, "ro")
        elif r < 2:
            plt.plot(i, r, "yo")
        else:
            plt.plot(i, r, "go")

    plt.axhline(y=analise["media_20"], color="r", linestyle="--",
                label=f"Média 20 = {analise['media_20']}")

    melhor_call = max(analise["calls"], key=lambda x: x[1])
    plt.title(f"Aviator - Últimos {len(ultimos20)} jogos | CALL: {melhor_call[0]}")

    plt.xlabel("Rodadas recentes")
    plt.ylabel("Multiplicador")
    plt.legend()
    plt.grid(True)
    plt.show()

# ==========================
# Execução Principal
# ==========================
if __name__ == "__main__":
    print("=== Robô Aviator Inteligente TURBO V9 (com Firebase) ===")
    print("Digite os resultados um por vez (ex: 1.23).")
    print("Digite 'sair' para encerrar.\n")

    resultados = []
    contador = 0

    while True:
        entrada = input("Resultado > ")

        if entrada.lower() == "sair":
            print("Robô encerrado. Histórico salvo em historico_aviator.csv 👋")
            break

        try:
            valor = float(entrada.replace(",", "."))
            resultados.append(valor)
            contador += 1

            avaliar_call(valor)

        except ValueError:
            print("⚠️ Digite apenas números válidos (ex: 2.45)")
            continue

        if contador == 3:  # análise a cada 3 rodadas
            analise = analisar_inteligente(resultados)

            if analise:
                print("\n=== ANÁLISE TURBO V9 ===")
                print(f"Prob >1.5x: {analise['prob_15x']}%")
                print(f"Prob >2x: {analise['prob_2x']}%")
                print(f"Prob >5x: {analise['prob_5x']}%")
                print(f"Prob >10x: {analise['prob_10x']}%")
                print(f"Prob ponderada: {analise['prob_ponderada']}%")
                print(f"Média últimos 20: {analise['media_20']}")
                print(f"Sequência baixa: {analise['sequencia_baixa']}")
                print(f"Frequências últimas 10: {analise['freq']}")
                print(f"Modo sugerido: {Fore.CYAN}{analise['modo']}{Style.RESET_ALL}")
                print("\nCalls do Robô:")
                for call, conf in analise["calls"]:
                    print(f" - {call} (Confiança: {conf:.2f}%)")

                salvar_csv(analise)
                plotar_grafico(resultados, analise)

            print("\n---\n")
            contador = 0
