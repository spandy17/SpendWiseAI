
const API = "http://127.0.0.1:8000";
let token = localStorage.getItem("spendwise_token");
let authMode = "login";
let categoryChart = null;
let monthlyChart=null;
let expensesCache = [];
let incomesCache = [];
let budgetsCache = [];

const $ = id => document.getElementById(id);
const money = amount => "₹" + Number(amount || 0).toLocaleString("en-IN", {maximumFractionDigits: 2});

async function request(path, options = {}) {
    const headers = {
        ...(options.body ? {"Content-Type": "application/json"} : {}),
        ...(token ? {Authorization: `Bearer ${token}`} : {}),
        ...options.headers
    };

    const response = await fetch(API + path, {...options, headers});

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || "Request failed");
    }

    if (response.status === 204) return null;

    if (response.headers.get("content-type")?.includes("text/csv")) {
        return response.blob();
    }

    return response.json();
}

function showMessage(message, success = false) {
    $("authMessage").textContent = message;
    $("authMessage").style.color = success ? "#159b65" : "#d44c3d";
}


function showAuth(mode) {
    authMode = mode;

    // Update active tabs
    $("loginTab").classList.toggle("active", mode === "login");
    $("signupTab").classList.toggle("active", mode === "signup");

    // Show or hide name field
    $("nameField").classList.toggle("hidden", mode !== "signup");

    // Update heading
    $("authHeading").textContent = mode === "login"
        ? "Login to your account"
        : "Create your account";

    // Update description
    $("authHeading").nextElementSibling.textContent = mode === "login"
        ? "Access your Expense AI workspace and manage your money more efficiently."
        : "Create your Expense AI account and start managing your finances.";

    // Update submit button
    $("authSubmit").textContent = mode === "login"
        ? "Sign In →"
        : "Create Account →";

    // Update top message
    showMessage("");
}


$("authForm").addEventListener("submit", async event => {
    event.preventDefault();

    const data = {
        email: $("email").value.trim(),
        password: $("password").value
    };

    if (authMode === "signup") {
        data.name = $("name").value.trim();
    }

    try {
        if (authMode === "signup") {
            await request("/auth/signup", {
                method: "POST",
                body: JSON.stringify(data)
            });
            showMessage("Registration successful! Please login.", true);
            showAuth("login");
        } else {
            const result = await request("/auth/login", {
                method: "POST",
                body: JSON.stringify(data)
            });

            token = result.access_token;
            localStorage.setItem("spendwise_token", token);
            await startApp();
        }
    } catch (error) {
        showMessage(error.message);
    }
});

async function startApp() {
    try {
        await request("/auth/me");
        $("authPage").classList.add("hidden");
        $("app").classList.remove("hidden");
        await loadDashboard();
    } catch {
        logout();
    }
}

function logout() {
    token = null;
    localStorage.removeItem("spendwise_token");
    $("app").classList.add("hidden");
    $("authPage").classList.remove("hidden");
}

function navigate(page, button) {
    document.querySelectorAll(".page").forEach(section => section.classList.add("hidden"));
    $(page).classList.remove("hidden");

    document.querySelectorAll(".nav").forEach(item => item.classList.remove("active"));
    if (button) button.classList.add("active");

    const titles = {
        dashboard: "Dashboard",
        expenses: "Expense Management",
        income: "Income Management",
        budgets: "Budget Planning",
        reports: "Financial Reports"
    };

    $("pageTitle").textContent = titles[page];

    if (page === "dashboard") loadDashboard();
    if (page === "expenses") loadExpenses();
    if (page === "income") loadIncome();
    if (page === "budgets") loadBudgets();
}




async function loadDashboard() {
    try {
        // 1. Fetch dashboard data
        const data = await request("/dashboard/");

        // 2. Update financial summary cards
        $("totalIncome").textContent = money(data.total_income);
        $("totalExpenses").textContent = money(data.total_expenses);
        $("balance").textContent = money(data.balance);
        $("transactions").textContent = data.total_transactions;

        // Negative balance styling
        $("balance").style.color = Number(data.balance) < 0
            ? "#dc3545"
            : "#159b65";

        // 3. Recent Expenses
        const recentExpenses = data.recent_expenses || [];

        $("recentExpenses").innerHTML = recentExpenses.length
            ? recentExpenses.map(item => `
                <div class="recent-item">
                    <div>
                        ${escapeHTML(item.title)}
                        <br>
                        <small>${escapeHTML(item.category)}</small>
                    </div>
                    <span>${money(item.amount)}</span>
                </div>
            `).join("")
            : "<p>No expenses recorded yet.</p>";

        // 4. Expense Category Doughnut Chart
        const categories = data.category_summary || [];
        const categoryCanvas = $("categoryChart");

        if (categoryChart) {
            categoryChart.destroy();
            categoryChart = null;
        }

        const oldMessage = categoryCanvas.parentElement
            .querySelector(".chart-empty");

        if (oldMessage) oldMessage.remove();

        if (categories.length > 0) {
            categoryCanvas.style.display = "block";

            categoryChart = new Chart(categoryCanvas, {
                type: "doughnut",
                data: {
                    labels: categories.map(item => item.category),
                    datasets: [{
                        data: categories.map(item => Number(item.amount)),
                        backgroundColor: [
                            "#159b65",
                            "#65c99a",
                            "#8ca9ed",
                            "#f2b86c",
                            "#d98e9c",
                            "#a89be8",
                            "#54b8c5"
                        ],
                        borderWidth: 2,
                        borderColor: "#ffffff",
                        hoverOffset: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: "bottom"
                        }
                    }
                }
            });
        } else {
            categoryCanvas.style.display = "none";

            const message = document.createElement("p");
            message.className = "chart-empty";
            message.textContent = "No category data available.";
            message.style.textAlign = "center";
            message.style.padding = "60px 10px";
            message.style.color = "#888";

            categoryCanvas.parentElement.appendChild(message);
        }

        // 5. Monthly Income vs Expenses Bar Chart
        const monthly = data.monthly_summary || [];

        if (monthlyChart) {
            monthlyChart.destroy();
            monthlyChart = null;
        }

        const monthlyCanvas = $("monthlyChart");

        monthlyChart = new Chart(monthlyCanvas, {
            type: "bar",
            data: {
                labels: monthly.map(item => item.month),
                datasets: [
                    {
                        label: "Income",
                        data: monthly.map(item => Number(item.income)),
                        backgroundColor: "#159b65",
                        borderRadius: 6
                    },
                    {
                        label: "Expenses",
                        data: monthly.map(item => Number(item.expenses)),
                        backgroundColor: "#e76f6f",
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom"
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        // 6. Monthly Budget Overview
        const budgets = data.budget_summary || [];
        const budgetContainer = $("budgetSummary");

        budgetContainer.innerHTML = budgets.length
            ? budgets.map(budget => {
                const percentage = Number(budget.percentage) || 0;
                const progress = Math.min(
                    Math.max(percentage, 0),
                    100
                );

                const color = budget.status === "exceeded"
                    ? "#dc3545"
                    : budget.status === "warning"
                    ? "#e9a23b"
                    : "#159b65";

                const message = budget.status === "exceeded"
                    ? "Budget exceeded!"
                    : budget.status === "warning"
                    ? "Approaching budget limit"
                    : "Within budget";

                return `
                    <div class="budget-item">
                        <div class="budget-info">
                            <strong>${escapeHTML(budget.category)}</strong>
                            <span>
                                ${money(budget.spent)} /
                                ${money(budget.limit)}
                            </span>
                        </div>

                        <div class="budget-progress">
                            <div style="
                                width: ${progress}%;
                                background: ${color};
                            "></div>
                        </div>

                        <div class="budget-footer">
                            <span>${percentage.toFixed(1)}% used</span>
                            <strong style="color: ${color}">
                                ${message}
                            </strong>
                        </div>
                    </div>
                `;
            }).join("")
            : "<p>No budgets created for this month yet.</p>";


        // Smart Spending Alerts
        const alertBudgets = data.budget_summary || [];

        const exceededBudgets = alertBudgets.filter(
            budget => budget.status === "exceeded"
        );

        const warningBudgets = alertBudgets.filter(
            budget => budget.status === "warning"
        );

        const alertContainer = $("budgetAlerts");

        if (exceededBudgets.length > 0) {
            alertContainer.innerHTML = `
                <div class="alert-card alert-danger">
                    <strong>Budget Exceeded!</strong>
                    <p>
                        ${exceededBudgets.map(b =>
                            escapeHTML(b.category)
                        ).join(", ")}
                        ${exceededBudgets.length === 1 ? "has" : "have"}
                        exceeded the monthly budget.
                    </p>
                </div>
            `;
        } else if (warningBudgets.length > 0) {
            alertContainer.innerHTML = `
                <div class="alert-card alert-warning">
                    <strong>Budget Warning</strong>
                    <p>
                        You are approaching your budget limit for
                        ${warningBudgets.map(b =>
                            escapeHTML(b.category)
                        ).join(", ")}.
                    </p>
                </div>
            `;
        } else {
            alertContainer.innerHTML = alertBudgets.length
                ? `
                    <div class="alert-card alert-success">
                        <strong>You're on track!</strong>
                        <p>All your monthly budgets are within their limits.</p>
                    </div>
                `
                : "";
        }




    } catch (error) {
        console.error("Dashboard loading error:", error);
        alert(error.message);
    }
}


function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;",
        '"': "&quot;", "'": "&#39;"
    })[char]);
}

$("expenseForm").addEventListener("submit", async event => {
    event.preventDefault();

    const id = $("expenseId").value;

    const data = {
        title: $("expenseTitle").value,
        amount: Number($("expenseAmount").value),
        category: $("expenseCategory").value,
        payment_method: $("paymentMethod").value,
        date: new Date($("expenseDate").value + "T12:00:00").toISOString(),
        description: $("expenseDescription").value
    };

    try {
        await request(id ? `/expenses/${id}` : "/expenses/", {
            method: id ? "PUT" : "POST",
            body: JSON.stringify(data)
        });

        event.target.reset();
        $("expenseId").value = "";
        await loadExpenses();
        alert("Expense saved successfully");
    } catch (error) {
        alert(error.message);
    }
});

async function loadExpenses() {
    try {
        const search = encodeURIComponent($("expenseSearch").value.trim());
        expensesCache = await request(`/expenses/?search=${search}`);

        $("expenseRows").innerHTML = expensesCache.map(item => `
            <tr>
                <td>${escapeHTML(item.title)}</td>
                <td>${money(item.amount)}</td>
                <td>${escapeHTML(item.category)}</td>
                <td>${new Date(item.date).toLocaleDateString("en-IN")}</td>
                <td>
                    <button class="action-btn edit-btn" onclick="editExpense(${item.id})">Edit</button>
                    <button class="action-btn delete-btn" onclick="deleteExpense(${item.id})">Delete</button>
                </td>
            </tr>
        `).join("") || '<tr><td colspan="5">No expenses found</td></tr>';
    } catch (error) {
        alert(error.message);
    }
}

function editExpense(id) {
    const item = expensesCache.find(x => x.id === id);
    if (!item) return;

    $("expenseId").value = item.id;
    $("expenseTitle").value = item.title;
    $("expenseAmount").value = item.amount;
    $("expenseCategory").value = item.category;
    $("paymentMethod").value = item.payment_method;
    $("expenseDate").value = item.date.slice(0, 10);
    $("expenseDescription").value = item.description || "";

    window.scrollTo({top: 0, behavior: "smooth"});
}

async function deleteExpense(id) {
    if (!confirm("Delete this expense?")) return;

    try {
        await request(`/expenses/${id}`, {method: "DELETE"});
        await loadExpenses();
    } catch (error) {
        alert(error.message);
    }
}

$("incomeForm").addEventListener("submit", async event => {
    event.preventDefault();

    const id = $("incomeId").value;
    const data = {
        source: $("incomeSource").value,
        amount: Number($("incomeAmount").value),
        date: new Date($("incomeDate").value + "T12:00:00").toISOString(),
        description: $("incomeDescription").value
    };

    try {
        await request(id ? `/income/${id}` : "/income/", {
            method: id ? "PUT" : "POST",
            body: JSON.stringify(data)
        });

        event.target.reset();
        $("incomeId").value = "";
        await loadIncome();
        alert("Income saved successfully");
    } catch (error) {
        alert(error.message);
    }
});

async function loadIncome() {
    try {
        incomesCache = await request("/income/");

        $("incomeRows").innerHTML = incomesCache.map(item => `
            <tr>
                <td>${escapeHTML(item.source)}</td>
                <td>${money(item.amount)}</td>
                <td>${new Date(item.date).toLocaleDateString("en-IN")}</td>
                <td>
                    <button class="action-btn edit-btn" onclick="editIncome(${item.id})">Edit</button>
                    <button class="action-btn delete-btn" onclick="deleteIncome(${item.id})">Delete</button>
                </td>
            </tr>
        `).join("") || '<tr><td colspan="4">No income found</td></tr>';
    } catch (error) {
        alert(error.message);
    }
}

function editIncome(id) {
    const item = incomesCache.find(x => x.id === id);
    if (!item) return;

    $("incomeId").value = item.id;
    $("incomeSource").value = item.source;
    $("incomeAmount").value = item.amount;
    $("incomeDate").value = item.date.slice(0, 10);
    $("incomeDescription").value = item.description || "";
    window.scrollTo({top: 0, behavior: "smooth"});
}

async function deleteIncome(id) {
    if (!confirm("Delete this income?")) return;

    try {
        await request(`/income/${id}`, {method: "DELETE"});
        await loadIncome();
    } catch (error) {
        alert(error.message);
    }
}

$("budgetForm").addEventListener("submit", async event => {
    event.preventDefault();

    const id = $("budgetId").value;
    const data = {
        category: $("budgetCategory").value,
        limit_amount: Number($("budgetLimit").value),
        month: Number($("budgetMonth").value),
        year: Number($("budgetYear").value)
    };

    try {
        await request(id ? `/budgets/${id}` : "/budgets/", {
            method: id ? "PUT" : "POST",
            body: JSON.stringify(data)
        });

        event.target.reset();
        $("budgetId").value = "";
        await loadBudgets();
        alert("Budget saved successfully");
    } catch (error) {
        alert(error.message);
    }
});

async function loadBudgets() {
    try {
        budgetsCache = await request("/budgets/");

        $("budgetRows").innerHTML = budgetsCache.map(item => `
            <tr>
                <td>${escapeHTML(item.category)}</td>
                <td>${money(item.limit_amount)}</td>
                <td>${item.month}</td>
                <td>${item.year}</td>
                <td>
                    <button class="action-btn edit-btn" onclick="editBudget(${item.id})">Edit</button>
                    <button class="action-btn delete-btn" onclick="deleteBudget(${item.id})">Delete</button>
                </td>
            </tr>
        `).join("") || '<tr><td colspan="5">No budgets found</td></tr>';
    } catch (error) {
        alert(error.message);
    }
}

function editBudget(id) {
    const item = budgetsCache.find(x => x.id === id);
    if (!item) return;

    $("budgetId").value = item.id;
    $("budgetCategory").value = item.category;
    $("budgetLimit").value = item.limit_amount;
    $("budgetMonth").value = item.month;
    $("budgetYear").value = item.year;
    window.scrollTo({top: 0, behavior: "smooth"});
}

async function deleteBudget(id) {
    if (!confirm("Delete this budget?")) return;

    try {
        await request(`/budgets/${id}`, {method: "DELETE"});
        await loadBudgets();
    } catch (error) {
        alert(error.message);
    }
}

function setupReports() {
    const months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];

    $("reportMonth").innerHTML = months.map((name, i) =>
        `<option value="${i + 1}">${name}</option>`
    ).join("");

    const now = new Date();
    $("reportMonth").value = now.getMonth() + 1;
    $("reportYear").value = now.getFullYear();
}

async function loadReport() {
    const month = $("reportMonth").value;
    const year = $("reportYear").value;

    try {
        const data = await request(`/reports/monthly?month=${month}&year=${year}`);

        $("reportResult").innerHTML = `
            <div class="report-summary">
                <div><p>Total Income</p><h3>${money(data.total_income)}</h3></div>
                <div><p>Total Expenses</p><h3>${money(data.total_expenses)}</h3></div>
                <div><p>Balance</p><h3>${money(data.balance)}</h3></div>
            </div>
        `;
    } catch (error) {
        alert(error.message);
    }
}

async function downloadCSV() {
    try {
        const blob = await request("/reports/csv");
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "Expense AI_report.csv";
        link.click();
        URL.revokeObjectURL(url);
    } catch (error) {
        alert(error.message);
    }
}

setupReports();

if (token) {
    startApp();
}
