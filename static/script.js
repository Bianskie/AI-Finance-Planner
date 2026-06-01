// ======
// VARIABEL GLOBAL UNTUK GRAFIK
// ======
let myChart = null; // Untuk grafik donat di report
let dashChart = null; // Untuk grafik batang di dashboard

// ======
// NAVIGASI & SIDEBAR
// ======
function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("active");
    document.getElementById("overlay").classList.toggle("active");
}

function closeSidebar() {
    document.getElementById("sidebar").classList.remove("active");
    document.getElementById("overlay").classList.remove("active");
}

function switchTab(tabId) {
    let sections = document.querySelectorAll('.page-section');
    sections.forEach(section => { section.style.display = 'none'; });
    document.getElementById(tabId).style.display = 'block';

    let navs = document.querySelectorAll('.nav-links li');
    navs.forEach(nav => { nav.classList.remove('active-tab'); });
    let activeNav = document.getElementById('nav-' + tabId);
    if(activeNav) {
        activeNav.classList.add('active-tab');
    }

    let titleElement = document.getElementById('page-title');
    if(titleElement) titleElement.innerText = tabId;
    
    closeSidebar();

    // Simpan nama halaman
    localStorage.setItem('activePage', tabId);
}

// ======
// Nggak langsung balik ke dashboard pas refresh
// ======
document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Cek ingatan halaman terakhir (kalau kosong, default ke 'dashboard')
    const savedPage = localStorage.getItem('activePage') || 'dashboard';
    
    switchTab(savedPage);

    // ======
    // Drag and Drop Overlay
    // ======
    const chatContainer = document.querySelector('.chat-container');
    const dragOverlay = document.getElementById('drag-overlay');
    const fileInput = document.getElementById('file-upload');
    
    if (chatContainer && dragOverlay && fileInput) {
        chatContainer.addEventListener('dragenter', (e) => {
            e.preventDefault();
            dragOverlay.classList.add('active'); 
        });
        dragOverlay.addEventListener('dragover', (e) => e.preventDefault());
        dragOverlay.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dragOverlay.classList.remove('active'); 
        });
        dragOverlay.addEventListener('drop', (e) => {
            e.preventDefault();
            dragOverlay.classList.remove('active'); 
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files; 
                fileInput.dispatchEvent(new Event('change'));
            }
        });
    }
});

// ======
// FETCH DATA & RENDER DASHBOARD (TABEL, CARD, GRAFIK BATANG, GOAL)
// ======
async function fetchTransactions() {
    try {
        const response = await fetch('/api/get_transactions');
        const data = await response.json();
        
        let totalIncome = 0;
        let totalExpense = 0;
        let tableHTML = '';

        // Variabel untuk mengelompokkan data per tanggal
        let dailyData = {};

        data.forEach(trx => {
            // 1. Hitung total keseluruhan untuk Card di atas
            if (trx.type === 'Income') { totalIncome += trx.amount; } 
            else { totalExpense += trx.amount; }

            // 2. Pisahkan data masuk ke tanggal masing-masing
            let date = trx.date; 
            if (!dailyData[date]) {
                dailyData[date] = { income: 0, expense: 0 };
            }
            if (trx.type === 'Income') {
                dailyData[date].income += trx.amount;
            } else {
                dailyData[date].expense += trx.amount;
            }

            // 3. Susun tabel HTML
            tableHTML += `
                <tr>
                    <td>${trx.date}</td>
                    <td>${trx.category}</td>
                    <td style="color: ${trx.type === 'Income' ? 'green' : 'red'}; font-weight: bold;">${trx.type}</td>
                    <td>Rp ${trx.amount.toLocaleString('id-ID')}</td>
                    <td><button onclick="deleteTransaction(${trx.id})" style="background:#FF0000; color:white; border:none; padding:5px 10px; border-radius:5px; cursor:pointer; font-weight:bold;">X</button></td>
                </tr>
            `;
        });

        const savedMoney = totalIncome - totalExpense;

        // Update Card Dashboard
        document.getElementById('total-pemasukan').innerText = 'Rp ' + totalIncome.toLocaleString('id-ID');
        document.getElementById('total-pengeluaran').innerText = 'Rp ' + totalExpense.toLocaleString('id-ID');
        document.getElementById('total-saldo').innerText = 'Rp ' + savedMoney.toLocaleString('id-ID');
        document.querySelector('#transaction-table tbody').innerHTML = tableHTML;

        // ======
        // Grafik Harian
        // ======
        
        // Urutkan tanggal dari yang terlama ke terbaru
        let sortedDates = Object.keys(dailyData).sort(); 
        let chartIncome = [];
        let chartExpense = [];

        // Masukkan nominal ke masing-masing tanggal
        sortedDates.forEach(date => {
            chartIncome.push(dailyData[date].income);
            chartExpense.push(dailyData[date].expense);
        });

        // Label kosong jika tidak ada data sama sekali
        if (sortedDates.length === 0) {
            sortedDates = ['No Data Yet'];
            chartIncome = [0];
            chartExpense = [0];
        }

        // Render Grafik Batang
        const ctxDash = document.getElementById('balanceChart');
        if (ctxDash) {
            if (dashChart != null) dashChart.destroy();
            dashChart = new Chart(ctxDash, {
                type: 'bar',
                data: {
                    labels: sortedDates, // Sumbu X sekarang berisi kumpulan Tanggal
                    datasets: [
                        { label: 'Income', data: chartIncome, backgroundColor: '#2ecc71', borderRadius: 5 },
                        { label: 'Expense', data: chartExpense, backgroundColor: '#e74c3c', borderRadius: 5 }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: { y: { beginAtZero: true } }
                }
            });
        }

        // Update Progress Bar di Halaman Tracking
        const goalRes = await fetch('/api/get_goal');
        const goalData = await goalRes.json();
        const currentGoal = goalData.goal;

        const progressFill = document.getElementById('progress-fill');
        const goalText = document.getElementById('goal-text');

        if (currentGoal > 0) {
            let percentage = (savedMoney / currentGoal) * 100;
            if (percentage < 0) percentage = 0;
            if (percentage > 100) percentage = 100;

            progressFill.style.width = percentage.toFixed(1) + '%';
            progressFill.innerText = percentage.toFixed(1) + '%';
            goalText.innerText = `Goal: Rp ${currentGoal.toLocaleString('id-ID')} | Saved: Rp ${savedMoney.toLocaleString('id-ID')}`;
        } else {
            progressFill.style.width = '0%';
            progressFill.innerText = '0%';
            goalText.innerText = `Goal: Not Set | Saved: Rp ${savedMoney.toLocaleString('id-ID')}`;
        }

    } catch (error) {
        console.error("Gagal mengambil data:", error);
    }
}

// Memanggil fungsi saat pertama kali membuka Web
fetchTransactions();

// ======
// FUNGSI HAPUS TRANSAKSI
// ======
async function deleteTransaction(trxId) {
    if (confirm("Are you sure you want to delete this transaction?")) {
        await fetch(`/api/delete_transaction/${trxId}`, { method: 'DELETE' });
        fetchTransactions();
    }
}

// ======
// INPUT DATA (PLANNING & GOAL)
// ======
document.getElementById('transactionForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const dataToSend = {
        type: document.getElementById('type').value,
        category: document.getElementById('category').value,
        amount: document.getElementById('amount').value,
        date: document.getElementById('date').value
    };

    const response = await fetch('/api/add_transaction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dataToSend)
    });

    const result = await response.json();
    if (result.status === 'success') {
        alert("Transaction successfully saved!");
        this.reset();
        fetchTransactions(); 
    }
});

document.getElementById('goalForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const newGoal = document.getElementById('goal-input').value;
    
    await fetch('/api/set_goal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal: newGoal })
    });
    
    alert('Savings Goal successfully updated!');
    this.reset();
    fetchTransactions(); 
});

// ======
// CHAT AI & FILE PREVIEW
// ======

function clearChat() {
    const chatHistoryDiv = document.getElementById('chat-history');
    if (chatHistoryDiv) {
        // 1. Kembalikan ke pesan sapaan default
        chatHistoryDiv.innerHTML = '<div class="msg ai-msg">Hello! I am your financial assistant. How can I help you today?</div>';
        
        // 2. Hapus memori chat dari browser
        localStorage.removeItem('chatData');
    }
}

document.getElementById('file-upload').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        document.getElementById('file-name').innerText = file.name;
        document.getElementById('file-preview').style.display = 'block';
        document.getElementById('chat-input').removeAttribute('required');
    }
});

function removeFile() {
    document.getElementById('file-upload').value = "";
    document.getElementById('file-preview').style.display = 'none';
    document.getElementById('chat-input').setAttribute('required', 'true');
}

document.getElementById('chatForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const inputField = document.getElementById('chat-input');
    const fileInput = document.getElementById('file-upload');
    const chatHistory = document.getElementById('chat-history');
    
    const message = inputField.value;
    const file = fileInput.files[0];
    if (!message && !file) return;

    let userMsgHTML = `<div class="msg user-msg">${message}</div>`;
    if (file) { userMsgHTML += `<div class="msg user-msg"><i>[File Attached: ${file.name}]</i></div>`; }
    chatHistory.innerHTML += userMsgHTML;
    chatHistory.scrollTop = chatHistory.scrollHeight;

    const loadingId = "loading-" + Date.now();
    chatHistory.innerHTML += `<div id="${loadingId}" class="msg ai-msg"><i>AI is processing...</i></div>`;
    chatHistory.scrollTop = chatHistory.scrollHeight;

    const formData = new FormData();
    formData.append('message', message);
    if (file) formData.append('file', file);

    try {
        const response = await fetch('/api/chat', { method: 'POST', body: formData });
        const data = await response.json();
        document.getElementById(loadingId).remove();
        
        let formattedText = data.response.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
        chatHistory.innerHTML += `<div class="msg ai-msg">${formattedText}</div>`;
    } catch (error) {
        document.getElementById(loadingId).remove();
        chatHistory.innerHTML += `<div class="msg ai-msg" style="color:red;">Error: Failed to connect to AI.</div>`;
    }

    // Reset Form Chat
    inputField.value = ""; 
    fileInput.value = "";
    document.getElementById('file-preview').style.display = 'none';
    document.getElementById('chat-input').setAttribute('required', 'true');
    chatHistory.scrollTop = chatHistory.scrollHeight;

    // ======
    // Menyimpan chat ke dalam memory
    // ======
    localStorage.setItem('chatData', chatHistory.innerHTML);
});

// ======
// MONTHLY REPORT & DOUGHNUT CHART
// ======
document.getElementById('generate-report').addEventListener('click', async function() {
    const reportContent = document.getElementById('report-content');
    reportContent.innerHTML = "<i>AI is analyzing your data and building charts... Please wait.</i>";

    // 1. Ambil data untuk Grafik
    const trxResponse = await fetch('/api/get_transactions');
    const trxData = await trxResponse.json();
    
    let totalInc = 0;
    let totalExp = 0;
    trxData.forEach(trx => {
        if (trx.type === 'Income') totalInc += trx.amount;
        else totalExp += trx.amount;
    });

    // 2. Gambar Grafik Doughnut
    const ctx = document.getElementById('expenseChart');
    ctx.style.display = 'block';
    
    if (myChart != null) { myChart.destroy(); }
    myChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Total Income', 'Total Expense'],
            datasets: [{
                data: [totalInc, totalExp],
                backgroundColor: ['#2ecc71', '#e74c3c'],
                borderWidth: 2
            }]
        }
    });

    // 3. Minta Laporan AI
    const formData = new FormData();
    const promptMessage = `
        Provide a comprehensive monthly financial evaluation report based on my data. 
        First, break down and explain exactly where the income and expenses came from based on the categories.
        Then, identify any wasteful spending and provide specific investment advice. 
        You MUST reply strictly in English. Use clear formatting.
    `;
    formData.append('message', promptMessage);

    try {
        const response = await fetch('/api/chat', { method: 'POST', body: formData });
        const data = await response.json();
        
        let formattedText = data.response
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>'); 
        reportContent.innerHTML = formattedText;
    } catch (error) {
        reportContent.innerHTML = "Failed to generate report. Check API connection.";
    }
});

// ======
// FITUR DRAG AND DROP
// ======
document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('DOMContentLoaded', () => {

    // 1. Mengingat halaman
    const savedPage = localStorage.getItem('activePage') || 'dashboard';
    switchTab(savedPage);

    // ======
    // Mengingat riwayat chat
    // ======
    const chatHistoryDiv = document.getElementById('chat-history');
    const savedChat = localStorage.getItem('chatData');
    
    if (savedChat && chatHistoryDiv) {
        chatHistoryDiv.innerHTML = savedChat;
    }

});
    const chatContainer = document.querySelector('.chat-container');
    const dragOverlay = document.getElementById('drag-overlay');
    const fileInput = document.getElementById('file-upload');

    if (chatContainer && dragOverlay && fileInput) {
       
        // 1. Menarik file di seluruh area chat
        chatContainer.addEventListener('dragenter', (e) => {
            e.preventDefault();
            dragOverlay.classList.add('active'); // Tampilkan layar hijau
        });

        // 2. Mencegah browser membuka gambar di tab baru
        dragOverlay.addEventListener('dragover', (e) => {
            e.preventDefault();
        });

        // 3. Saat file ditarik keluar dari area chat (Batal)
        dragOverlay.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dragOverlay.classList.remove('active'); // Sembunyikan layar hijau
        });

        // 4. Saat file dilepaskan (Di-drop)
        dragOverlay.addEventListener('drop', (e) => {
            e.preventDefault();
            dragOverlay.classList.remove('active'); // Sembunyikan layar hijau

            // Ambil filenya dan masukkan ke input tersembunyi
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files; 
                const event = new Event('change');
                fileInput.dispatchEvent(event);
            }
        });
    }
});

// ======
// PEMICU OTOMATIS SAAT REFRESH WEB
// ======
document.addEventListener('DOMContentLoaded', () => {
    
    // 1. LOAD HALAMAN TERAKHIR
    const savedPage = localStorage.getItem('activePage') || 'dashboard';
    if (typeof switchTab === "function") {
        switchTab(savedPage);
    }

    // ======
    // 2. LOAD RIWAYAT CHAT
    // ======
    const chatHistoryDiv = document.getElementById('chat-history');
    const savedChat = localStorage.getItem('chatData');
    
    if (savedChat && chatHistoryDiv) {
        // Tempelkan memori chat ke HTML
        chatHistoryDiv.innerHTML = savedChat;
        // Otomatis scroll ke pesan paling bawah
        chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
    }
   
    // ======
    // 3. KODINGAN DRAG & DROP
    // ======
    const chatContainer = document.querySelector('.chat-container');
    const dragOverlay = document.getElementById('drag-overlay');
    const fileInput = document.getElementById('file-upload');
    
    if (chatContainer && dragOverlay && fileInput) {
        chatContainer.addEventListener('dragenter', (e) => { e.preventDefault(); dragOverlay.classList.add('active'); });
        dragOverlay.addEventListener('dragover', (e) => e.preventDefault());
        dragOverlay.addEventListener('dragleave', (e) => { e.preventDefault(); dragOverlay.classList.remove('active'); });
        dragOverlay.addEventListener('drop', (e) => {
            e.preventDefault();
            dragOverlay.classList.remove('active'); 
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files; 
                fileInput.dispatchEvent(new Event('change'));
            }
        });
    }
});