// Importa SDK do Firebase
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getAuth, signInWithPopup, GoogleAuthProvider, signOut, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
import { getFirestore, doc, getDoc, collection, query, orderBy, limit, onSnapshot } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";

// Configuração Firebase
const firebaseConfig = {
  apiKey: "AIzaSyD-yt8AmgRkMnJH9xKwDSKn9_X42Cmpq7Y",
  authDomain: "robo-aviator2025.firebaseapp.com",
  projectId: "robo-aviator2025",
  storageBucket: "robo-aviator2025.firebasestorage.app",
  messagingSenderId: "303072216239",
  appId: "1:303072216239:web:d6e659c5dd49be14e7005a",
  measurementId: "G-094LT3104Y"
};

// Inicializa Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

// Elementos
const loginScreen = document.getElementById("login");
const dashboard = document.getElementById("dashboard");
const callList = document.getElementById("callList");
const stats = document.getElementById("stats");

// 🔑 Login Google (melhor que anônimo para identificar usuário)
window.login = () => {
  const provider = new GoogleAuthProvider();
  signInWithPopup(auth, provider).catch(err => console.error("Erro no login:", err));
};

// Logout
window.logout = () => {
  signOut(auth);
};

// Monitora login e checa assinatura
onAuthStateChanged(auth, async (user) => {
  if (user) {
    console.log("Logado:", user.email);

    // Verifica assinatura no Firestore
    const ref = doc(db, "assinaturas", user.uid);
    const snap = await getDoc(ref);

    if (snap.exists()) {
      const dados = snap.data();
      const hoje = new Date();

      if (dados.status === "ativo" && dados.validade.toDate() > hoje) {
        console.log("✅ Assinatura válida, liberando acesso...");
        loginScreen.classList.add("hidden");
        dashboard.classList.remove("hidden");
        carregarCalls();
      } else {
        alert("⚠️ Sua assinatura expirou ou está pendente.");
        loginScreen.classList.remove("hidden");
        dashboard.classList.add("hidden");
      }
    } else {
      alert("⚠️ Nenhuma assinatura encontrada. Faça o pagamento.");
      loginScreen.classList.remove("hidden");
      dashboard.classList.add("hidden");
    }
  } else {
    loginScreen.classList.remove("hidden");
    dashboard.classList.add("hidden");
  }
});

// 🔥 Carregar calls em tempo real
function carregarCalls() {
  const q = query(collection(db, "calls"), orderBy("hora", "desc"), limit(10));
  onSnapshot(q, (snapshot) => {
    callList.innerHTML = "";
    let acertos = 0, erros = 0;

    snapshot.forEach(doc => {
      const data = doc.data();
      const li = document.createElement("li");
      li.textContent = `${data.call} | Confiança: ${data.confianca}% | Resultado: ${data.resultado || "?"}`;
      callList.appendChild(li);

      if (data.resultado === "ACERTOU") acertos++;
      if (data.resultado === "ERROU") erros++;
    });

    const total = acertos + erros;
    const taxa = total > 0 ? ((acertos / total) * 100).toFixed(2) : "--";
    stats.textContent = `Taxa de acerto: ${taxa}% (${acertos} acertos / ${erros} erros)`;
  });
}
