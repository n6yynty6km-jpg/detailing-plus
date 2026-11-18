
// Демонстрационные цены для калькулятора.

const prices = {
    wash: {
        small: 1000,
        medium: 1300,
        large: 1600
    },
    cleaning: {
        small: 5000,
        medium: 6500,
        large: 8000
    },
    polishing: {
        small: 8000,
        medium: 11000,
        large: 14000
    },
    coating: {
        small: 7000,
        medium: 9000,
        large: 12000
    }
};

// Элементы калькулятора.

const serviceSelect = document.querySelector("#service");
const sizeSelect = document.querySelector("#car-size");
const priceElement = document.querySelector("#price");

// Элементы формы записи.

const bookingForm = document.querySelector("#booking-form");
const bookingService = document.querySelector("#booking-service");
const bookingCarSize = document.querySelector("#booking-car-size");
const bookingDate = document.querySelector("#booking-date");
const bookingTime = document.querySelector("#booking-time");
const bookingMessage = document.querySelector("#booking-message");

// Пересчёт стоимости.

function calculatePrice() {
    const service = serviceSelect.value;
    const size = sizeSelect.value;

    const price = prices[service][size];

    priceElement.textContent =
        price.toLocaleString("ru-RU") + " ₽";
}

serviceSelect.addEventListener("change", calculatePrice);
sizeSelect.addEventListener("change", calculatePrice);

// Выбор услуги в каталоге.

document.querySelectorAll(".service-select").forEach(button => {
    button.addEventListener("click", () => {
        serviceSelect.value = button.dataset.service;
        bookingService.value = button.dataset.service;

        calculatePrice();

        document.querySelector("#calculator").scrollIntoView({
            behavior: "smooth"
        });
    });
});

// Синхронизация калькулятора и формы записи.

bookingService.addEventListener("change", () => {
    serviceSelect.value = bookingService.value;
    calculatePrice();
});

bookingCarSize.addEventListener("change", () => {
    sizeSelect.value = bookingCarSize.value;
    calculatePrice();
});

// Устанавливаем минимальную дату — сегодня.

const today = new Date();
const localDate = new Date(
    today.getTime() - today.getTimezoneOffset() * 60000
).toISOString().split("T")[0];

bookingDate.min = localDate;

// Сброс списка времени.

function resetTimeOptions(message) {
    bookingTime.innerHTML = "";

    const option = document.createElement("option");
    option.value = "";
    option.textContent = message;

    bookingTime.appendChild(option);
    bookingTime.disabled = true;
}

// Получение свободного времени с сервера.

async function loadAvailableSlots() {
    const selectedDate = bookingDate.value;
    const service = bookingService.value;
    const carSize = bookingCarSize.value;

    if (!selectedDate) {
        resetTimeOptions("Сначала выберите дату");
        return;
    }

    resetTimeOptions("Загружаем свободное время...");

    try {
        const params = new URLSearchParams({
            service_code: service,
            car_size: carSize,
            target_date: selectedDate
        });

        const response = await fetch(
            `/api/slots?${params.toString()}`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Не удалось получить расписание");
        }

        bookingTime.innerHTML = "";

        if (data.slots.length === 0) {
            resetTimeOptions("Свободного времени нет");
            return;
        }

        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "Выберите время";
        bookingTime.appendChild(placeholder);

        data.slots.forEach(slot => {
            const option = document.createElement("option");

            option.value = slot.start + ":00";
            option.textContent = `${slot.start} — ${slot.end}`;

            bookingTime.appendChild(option);
        });

        bookingTime.disabled = false;

    } catch (error) {
        resetTimeOptions("Ошибка загрузки расписания");
        console.error("Ошибка получения времени:", error);
    }
}

// Обновляем время при изменении даты или услуги.

bookingDate.addEventListener("change", loadAvailableSlots);
bookingService.addEventListener("change", loadAvailableSlots);
bookingCarSize.addEventListener("change", loadAvailableSlots);

// Отправка заявки.

bookingForm.addEventListener("submit", async event => {
    event.preventDefault();

    bookingMessage.textContent = "Отправляем заявку...";
    bookingMessage.className = "booking-message";

    const submitButton = bookingForm.querySelector(
        'button[type="submit"]'
    );

    submitButton.disabled = true;

    const formData = {
        client_name: document.querySelector("#client-name").value.trim(),
        client_phone: document.querySelector("#client-phone").value.trim(),
        service_code: bookingService.value,
        car_brand: document.querySelector("#car-brand").value.trim(),
        car_model: document.querySelector("#car-model").value.trim(),
        car_size: bookingCarSize.value,
        appointment_date: bookingDate.value,
        start_time: bookingTime.value,
        comment: document.querySelector("#booking-comment").value.trim() || null
    };

    try {
        const response = await fetch("/api/appointments", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Не удалось отправить заявку");
        }

        bookingMessage.textContent =
            `Заявка №${data.appointment_id} отправлена! ` +
            `Услуга: ${data.service}. ` +
            `Время: ${data.start}–${data.end}. ` +
            `Предварительная стоимость: ${Number(data.price).toLocaleString("ru-RU")} ₽. ` +
            "Мы свяжемся с вами для подтверждения.";

        bookingMessage.classList.add("success");

        bookingForm.reset();
        bookingDate.min = localDate;
        resetTimeOptions("Сначала выберите дату");

        serviceSelect.value = bookingService.value;
        sizeSelect.value = bookingCarSize.value;
        calculatePrice();

    } catch (error) {
        bookingMessage.textContent = error.message;
        bookingMessage.classList.add("error");

        // Если время успели занять, обновляем список.
        await loadAvailableSlots();

    } finally {
        submitButton.disabled = false;
    }
});

// Первоначальный расчёт.

calculatePrice();


// Получаем актуальные услуги и цены из PostgreSQL.

async function loadPublicServices() {
    try {
        const response = await fetch("/api/services");

        if (!response.ok) {
            throw new Error("Не удалось загрузить прайс");
        }

        const services = await response.json();

        if (services.length === 0) {
            throw new Error("Сейчас нет доступных услуг");
        }

        // Обновляем цены калькулятора.
        Object.keys(prices).forEach(code => delete prices[code]);

        services.forEach(service => {
            prices[service.code] = {
                small: Number(service.price_small),
                medium: Number(service.price_medium),
                large: Number(service.price_large)
            };
        });

        // Обновляем списки услуг на сайте.
        [serviceSelect, bookingService].forEach(select => {
            const previousValue = select.value;
            select.replaceChildren();

            services.forEach(service => {
                const option = document.createElement("option");
                option.value = service.code;
                option.textContent = service.name;
                select.appendChild(option);
            });

            if (services.some(service => service.code === previousValue)) {
                select.value = previousValue;
            }
        });

        calculatePrice();

    } catch (error) {
        console.error("Ошибка загрузки прайса:", error);
    }
}

loadPublicServices();

