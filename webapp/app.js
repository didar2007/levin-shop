
let products = [];
let cart = [];

const productGrid = document.getElementById("productGrid");
const catalogTitle = document.getElementById("catalogTitle");

// ПОСТОЯННЫЙ BACKEND RAILWAY
const API_URL = "https://levin-shop-production.up.railway.app";

// TELEGRAM WEB APP
function getTelegramWebApp() {
    return window.Telegram?.WebApp || null;
}

function getTelegramInitData() {
    const telegram = getTelegramWebApp();

    if (!telegram) {
        return "";
    }

    telegram.ready();
    telegram.expand();

    return telegram.initData || "";
}

const tg = getTelegramWebApp();
console.log("LEVIN Telegram diagnostics:", {
    telegramExists: !!window.Telegram,
    webAppExists: !!window.Telegram?.WebApp,
    initDataLength: window.Telegram?.WebApp?.initData?.length || 0,
    platform: window.Telegram?.WebApp?.platform || "unknown"
});

if (tg) {
    tg.ready();
    tg.expand();
}

// КОНТАКТ АДМИНИСТРАТОРА
const ADMIN_URL = "https://t.me/toxicalien21";

// ТЕКУЩАЯ КАТЕГОРИЯ
let currentCategory = "all";

// ЗАГРУЗКА ТОВАРОВ
async function loadProducts() {
    try {
        const response = await fetch("./products.json");

        if (!response.ok) {
            throw new Error("Не удалось загрузить каталог");
        }

        products = await response.json();

        filterCategory("all", false);

    } catch (error) {
        console.error("Ошибка загрузки товаров:", error);
        productGrid.innerHTML = "<p>Не удалось загрузить товары.</p>";
    }
}

// ОТОБРАЖЕНИЕ ТОВАРОВ
function renderProducts(items) {
    productGrid.innerHTML = "";

    if (items.length === 0) {
        productGrid.innerHTML = `
            <div class="empty-products">
                <span>🛍️</span>
                <h3>Пока нет товаров</h3>
                <p>Скоро здесь появятся новые товары LEVIN.</p>
            </div>
        `;
        return;
    }

    items.forEach(product => {
        const card = document.createElement("div");

        card.className = "product-card";

        card.innerHTML = `
            <img class="product-image"
                 src="${product.image}"
                 alt="${product.name}"
                 loading="lazy">

            <div class="product-info">
                <div class="product-name">${product.name}</div>

                <div class="product-description">
                    ${product.description}
                </div>

                <div class="product-bottom">
                    <span class="product-price">
                        ${product.price.toLocaleString("ru-RU")} ₸
                    </span>

                    <button class="add-button" type="button">+</button>
                </div>
            </div>
        `;

        card.querySelector(".add-button").addEventListener("click", () => {
            addToCart(product.id);
        });

        productGrid.appendChild(card);
    });
}

// ПЕРЕКЛЮЧЕНИЕ КАТЕГОРИЙ
function filterCategory(category, shouldScroll = true) {
    currentCategory = category;

    let filteredProducts;

    if (category === "all") {
        filteredProducts = products;
        catalogTitle.textContent = "Все товары LEVIN";

    } else if (category === "newyear") {
        filteredProducts = products.filter(
            product => product.category === "newyear"
        );
        catalogTitle.textContent = "🎄 Новогодние товары";

    } else if (category === "home") {
        filteredProducts = products.filter(
            product => product.category === "home"
        );
        catalogTitle.textContent = "🏠 Товары для дома";

    } else if (category === "sport") {
        filteredProducts = products.filter(
            product => product.category === "sport"
        );
        catalogTitle.textContent = "🏋️ Спортивные товары";

    } else {
        filteredProducts = [];
    }

    const newyearButton = document.getElementById("categoryNewyear");
    const homeButton = document.getElementById("categoryHome");
    const sportButton = document.getElementById("categorySport");
    const allButton = document.getElementById("allProductsButton");

    newyearButton?.classList.toggle("active", category === "newyear");
    homeButton?.classList.toggle("active", category === "home");
    sportButton?.classList.toggle("active", category === "sport");
    allButton?.classList.toggle("active", category === "all");

    renderProducts(filteredProducts);

    if (shouldScroll) {
        scrollToCatalog();
    }
}

// ДОБАВЛЕНИЕ В КОРЗИНУ
function addToCart(productId) {
    const product = products.find(p => p.id === productId);

    if (!product || product.stock <= 0) {
        alert("Товар закончился");
        return;
    }

    const existing = cart.find(item => item.id === productId);

    if (existing) {
        if (existing.quantity >= product.stock) {
            alert("Больше товаров нет в наличии");
            return;
        }

        existing.quantity++;
    } else {
        cart.push({
            ...product,
            quantity: 1
        });
    }

    renderCart();
}

// НАВИГАЦИЯ
function scrollToCatalog() {
    document.getElementById("catalog").scrollIntoView({
        behavior: "smooth"
    });
}

function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}

// КОРЗИНА
function openCart() {
    document.getElementById("cartOverlay").classList.add("show");
    renderCart();
}

function closeCart() {
    document.getElementById("cartOverlay").classList.remove("show");
}

function renderCart() {
    const cartBadge = document.getElementById("cartBadge");

    const cartCount = cart.reduce(
        (sum, item) => sum + item.quantity,
        0
    );

    if (cartBadge) {
        cartBadge.textContent = cartCount > 99 ? "99+" : cartCount;
        cartBadge.classList.toggle("visible", cartCount > 0);
    }

    const cartItems = document.getElementById("cartItems");
    const cartEmpty = document.getElementById("cartEmpty");
    const cartSummary = document.getElementById("cartSummary");
    const cartTotal = document.getElementById("cartTotal");

    cartItems.innerHTML = "";

    if (cart.length === 0) {
        cartEmpty.style.display = "block";
        cartSummary.style.display = "none";
        return;
    }

    cartEmpty.style.display = "none";
    cartSummary.style.display = "block";

    cart.forEach(item => {
        const element = document.createElement("div");

        element.className = "cart-item";

        element.innerHTML = `
            <img src="${item.image}" alt="${item.name}">

            <div class="cart-item-info">
                <h3>${item.name}</h3>

                <div class="cart-item-price">
                    ${(item.price * item.quantity).toLocaleString("ru-RU")} ₸
                </div>

                <div class="cart-controls">
                    <button onclick="changeQuantity(${item.id}, -1)">−</button>
                    <span>${item.quantity}</span>
                    <button onclick="changeQuantity(${item.id}, 1)">+</button>
                    <button class="remove-item"
                        onclick="removeFromCart(${item.id})">✕</button>
                </div>
            </div>
        `;

        cartItems.appendChild(element);
    });

    const total = cart.reduce(
        (sum, item) => sum + item.price * item.quantity, 0
    );

    cartTotal.textContent = total.toLocaleString("ru-RU") + " ₸";
}

function changeQuantity(productId, change) {
    const item = cart.find(item => item.id === productId);

    if (!item) return;

    const product = products.find(p => p.id === productId);

    if (change > 0 && item.quantity >= product.stock) {
        alert("Больше товаров нет в наличии");
        return;
    }

    item.quantity += change;

    if (item.quantity <= 0) {
        cart = cart.filter(item => item.id !== productId);
    }

    renderCart();
}

function removeFromCart(productId) {
    cart = cart.filter(item => item.id !== productId);
    renderCart();
}

// ОФОРМЛЕНИЕ ЗАКАЗА
function checkout() {
    if (cart.length === 0) {
        alert("Ваша корзина пуста");
        return;
    }

    const total = cart.reduce(
        (sum, item) => sum + item.price * item.quantity, 0
    );

    document.getElementById("checkoutTotal").textContent =
        total.toLocaleString("ru-RU") + " ₸";

    closeCart();

    document.getElementById("checkoutOverlay").classList.add("show");
}

function closeCheckout() {
    document.getElementById("checkoutOverlay").classList.remove("show");
}

// ОТПРАВКА ЗАКАЗА НА СЕРВЕР
const checkoutForm = document.getElementById("checkoutForm");

checkoutForm.addEventListener("submit", async function(event) {
    event.preventDefault();

    if (cart.length === 0) {
        alert("Корзина пуста");
        return;
    }

    // Получаем актуальные данные Telegram при отправке
    const initData = getTelegramInitData();

    if (!initData) {
        alert(
            "Не удалось получить данные Telegram.\n\n" +
            "Закройте каталог и откройте его повторно через кнопку Telegram."
        );
        return;
    }

    const submitButton = checkoutForm.querySelector(".checkout-submit");

    const order = {
        initData: initData,
        name: document.getElementById("customerName").value.trim(),
        phone: document.getElementById("customerPhone").value.trim(),
        street: document.getElementById("customerStreet").value.trim(),
        apartment: document.getElementById("customerApartment").value.trim(),
        floor: document.getElementById("customerFloor").value.trim(),
        entrance: document.getElementById("customerEntrance").value.trim(),
        contact_method: document.getElementById("contactMethod").value,
        comment: document.getElementById("customerComment").value.trim(),

        items: cart.map(item => ({
            id: item.id,
            name: item.name,
            price: item.price,
            quantity: item.quantity
        }))
    };

    submitButton.disabled = true;
    submitButton.textContent = "Отправляем заказ...";

    try {
        const response = await fetch(`${API_URL}/api/orders`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(order)
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(
                result.detail || "Не удалось оформить заказ"
            );
        }

        cart = [];
        renderCart();
        checkoutForm.reset();
        closeCheckout();

        const successMessage =
            `Ваш заказ №${result.order_number} успешно отправлен!`;

        const telegram = getTelegramWebApp();

        if (telegram && telegram.showPopup) {
            telegram.showPopup({
                title: "Спасибо за заказ! 🎄",
                message: successMessage,
                buttons: [{ type: "ok", text: "Отлично" }]
            });
        } else {
            alert(successMessage);
        }

    } catch (error) {
        console.error("Ошибка оформления:", error);

        alert(
            error.message === "Telegram authorization required" ||
            error.message === "Telegram data verification failed" ||
            error.message === "Telegram session expired"
                ? "Сессия Telegram устарела. Закройте каталог и откройте его снова."
                : "Не удалось отправить заказ. Попробуйте ещё раз."
        );

    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Подтвердить заказ →";
    }
});

// СВЯЗЬ С АДМИНИСТРАТОРОМ
function contactAdmin() {
    const telegram = getTelegramWebApp();

    if (telegram && telegram.openTelegramLink) {
        telegram.openTelegramLink(ADMIN_URL);
    } else {
        window.open(ADMIN_URL, "_blank");
    }
}

// ЗАПУСК
loadProducts();
