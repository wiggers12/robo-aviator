// Importa SDK do Firebase
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { 
  getAuth, 
  signInWithEmailAndPassword, 
  signInWithPopup, 
  GoogleAuthProvider, 
  signOut, 
  onAuthStateChanged 
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";

import { 
  getFirestore, 
  collection, 
  query, 
  where, 
  getDocs, 
  doc, 
  updateDoc, 
  orderBy, 
  limit, 
  onSnapshot 
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";

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

// Elementos da interface
const loginScreen = document.getElementById("login");
const dashboard = document.getElementById("dashboard");
const adminPanel = document.getElementById("admin");
const callList = document.getElementById("callList");
const stats = document.getElementById("stats");

// === LOGIN COM EMAIL E SENHA ===
window.loginEmail = async function () {
  const email = document.getElementById("email").value;
  const senha = document.getElementById("senha").value;

  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, senha);
    verificarAcesso(userCredential.user.email);
  } catch (err) {
    alert("❌ Erro no login: " + err.message);
  }
};

// === LOGIN COM GOOGLE ===
window.loginGoogle = () => {
  const provider = new GoogleAuthProvider();
  signInWithPopup(auth, provider).catch(err => console.error("Erro no login:", err));
};

// === LOGOUT ===
window.logout = () => {
  signOut(auth);
};

// === MONITORAR LOGIN ===
onAuthStateChanged(auth, (user) => {
  if (user) {
    verificarAcesso(user.email);
  } else {
    showLogin();
  }
});

// === VERIFICAR ACESSO ===
async function verificarAcesso(email) {
  // 👑 Se for admin → abre painel admin
  if (email === "seuemail@admin.com") { // <-- troque pelo seu email de admin
    carregarAssinaturas();
    showAdmin();
    return;
  }

  // Usuário normal → verificar assinatura
  const q = query(collection(db, "assinaturas"), where("email", "==", email));
  const snap = await getDocs(q);

  if (!snap.empty) {
    const dados = snap.docs[0].data();
    const hoje = new Date();
    const validade = dados.validade?.toDate ? dados.validade.toDate() : new Date(dados.validade);

    if (dados.status === "ATIVO" && validade > hoje) {
      showDashboard();
      carregarCalls();
    } else {
      alert("⚠️ Sua assinatura expirou ou está inativa.");
      showLogin();
    }
  } else {
    alert("⚠️ Nenhuma assinatura encontrada.");
    showLogin();
  }
}

// === ADMIN: LISTAR ASSINATURAS ===
async function carregarAssinaturas() {
  const assinaturasRef = collection(db, "assinaturas");
  const snapshot = await getDocs(assinaturasRef);
  const table = document.getElementById("assinaturasTable");
  table.innerHTML = "";

  snapshot.forEach(docSnap => {
    const data = docSnap.data();
    const row = `
      <tr>
        <td>${data.email}</td>
        <td>${data.status}</td>
        <td>${data.validade || "Não definido"}</td>
        <td>
          <button onclick="atualizarStatus('${docSnap.id}', 'ATIVO')">Ativar</button>
          <button onclick="atualizarStatus('${docSnap.id}', 'INATIVO')">Inativar</button>
        </td>
      </tr>
    `;
    table.innerHTML += row;
  });
}

// === ADMIN: ATUALIZAR STATUS ===
window.atualizarStatus = async function (id, novoStatus) {
  const ref = doc(db, "assinaturas", id);
  await updateDoc(ref, { status: novoStatus });
  alert(`✅ Usuário atualizado para ${novoStatus}`);
  carregarAssinaturas();
};

// === DASHBOARD: CARREGAR CALLS EM TEMPO REAL ===
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

// === CONTROLE DE TELAS ===
function showDashboard() {
  loginScreen.classList.add("hidden");
  adminPanel.classList.add("hidden");
  dashboard.classList.remove("hidden");
}

function showAdmin() {
  loginScreen.classList.add("hidden");
  dashboard.classList.add("hidden");
  adminPanel.classList.remove("hidden");
}

function showLogin() {
  dashboard.classList.add("hidden");
  adminPanel.classList.add("hidden");
  loginScreen.classList.remove("hidden");
}
