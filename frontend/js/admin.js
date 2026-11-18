
let adminAuthorization = "";

const loginForm = document.querySelector("#login-form");
const loginSection = document.querySelector("#login-section");
const dashboard = document.querySelector("#dashboard");
const loginMessage = document.querySelector("#login-message");
const dashboardMessage = document.querySelector("#dashboard-message");
const appointmentsTable = document.querySelector("#appointments-table");

const statuses = {
    new: "Новая",
    confirmed: "Подтверждена",
    completed: "Завершена",
    cancelled: "Отменена"
};

// Выполняем запросы к защищённому API.

async function adminFetch(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            "Authorization": adminAuthorization
        }
    });

    if (response.status === 401) {
        throw new Error("Неверный логин или пароль");
    }

    return response;
}

// Вход администратора.

loginForm.addEventListener("submit", async event => {
    event.preventDefault();

    const username = document.querySelector("#username").value;
    const password = document.querySelector("#password").value;

    adminAuthorization =
        "Basic " + btoa(username + ":" + password);

    loginMessage.textContent = "Проверяем данные...";
    loginMessage.className = "message";

    try {
        const response = await adminFetch(
            "/api/admin/appointments"
        );

        if (!response.ok) {
            throw new Error("Не удалось загрузить заявки");
        }

        const appointments = await response.json();

        loginSection.hidden = true;
        dashboard.hidden = false;

        renderAppointments(appointments);
        await loadServices();

    } catch (error) {
        adminAuthorization = "";
        loginMessage.textContent = error.message;
        loginMessage.classList.add("error");
    }
});

// Отображение заявок.

function renderAppointments(appointments) {
    appointmentsTable.replaceChildren();

    if (appointments.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = 7;
        cell.className = "empty-message";
        cell.textContent = "Пока заявок нет.";

        row.appendChild(cell);
        appointmentsTable.appendChild(row);
        return;
    }

    appointments.forEach(appointment => {
        const row = document.createElement("tr");

        const values = [
            appointment.id,
            `${appointment.client_name}\n${appointment.client_phone}`,
            `${appointment.car}\n${appointment.car_size}`,
            appointment.service,
            `${appointment.date}\n${appointment.start}–${appointment.end}`,
            Number(appointment.price).toLocaleString("ru-RU") + " ₽"
        ];

        values.forEach(value => {
            const cell = document.createElement("td");
            cell.textContent = value;
            row.appendChild(cell);
        });

        const statusCell = document.createElement("td");
        const statusSelect = document.createElement("select");

        Object.entries(statuses).forEach(([value, label]) => {
            const option = document.createElement("option");
            option.value = value;
            option.textContent = label;

            if (value === appointment.status) {
                option.selected = true;
            }

            statusSelect.appendChild(option);
        });

        statusSelect.addEventListener("change", () => {
            updateStatus(
                appointment.id,
                statusSelect.value,
                statusSelect
            );
        });

        statusCell.appendChild(statusSelect);
        row.appendChild(statusCell);

        if (appointment.comment) {
            row.title = "Комментарий: " + appointment.comment;
        }

        appointmentsTable.appendChild(row);
    });
}

// Изменение статуса заявки.

async function updateStatus(appointmentId, status, select) {
    select.disabled = true;

    try {
        const response = await adminFetch(
            `/api/admin/appointments/${appointmentId}/status`,
            {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ status })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Не удалось изменить статус");
        }

        dashboardMessage.textContent =
            `Статус заявки №${appointmentId} обновлён.`;

        dashboardMessage.className = "message success";

    } catch (error) {
        dashboardMessage.textContent = error.message;
        dashboardMessage.className = "message error";

        await loadAppointments();

    } finally {
        select.disabled = false;
    }
}

// Обновление списка.

async function loadAppointments() {
    try {
        const response = await adminFetch(
            "/api/admin/appointments"
        );

        if (!response.ok) {
            throw new Error("Не удалось обновить список");
        }

        const appointments = await response.json();
        renderAppointments(appointments);

    } catch (error) {
        dashboardMessage.textContent = error.message;
        dashboardMessage.className = "message error";
    }
}

// Выход из панели.

document.querySelector("#logout-button").addEventListener("click", () => {
    adminAuthorization = "";

    appointmentsTable.replaceChildren();
    dashboard.hidden = true;
    loginSection.hidden = false;

    loginForm.reset();
    loginMessage.textContent = "";
    dashboardMessage.textContent = "";
});


// Загрузка услуг из PostgreSQL.

async function loadServices() {
    const container = document.querySelector("#services-list");

    container.textContent = "Загружаем услуги...";

    try {
        const response = await adminFetch("/api/admin/services");

        if (!response.ok) {
            throw new Error("Не удалось загрузить услуги");
        }

        const services = await response.json();

        container.replaceChildren();

        services.forEach(service => {
            const card = document.createElement("article");
            card.className = "service-admin-card";

            const heading = document.createElement("h3");
            heading.textContent = service.name;

            const code = document.createElement("p");
            code.className = "service-code";
            code.textContent = `Код услуги: ${service.code}`;

            const fields = document.createElement("div");
            fields.className = "service-admin-fields";

            function addField(labelText, value, name, type = "text") {
                const wrapper = document.createElement("label");
                wrapper.className = "service-admin-field";

                const label = document.createElement("span");
                label.textContent = labelText;

                const input = document.createElement("input");
                input.type = type;
                input.name = name;
                input.value = value;

                if (type === "number") {
                    input.min = "0";
                    input.step = name.startsWith("price_") ? "0.01" : "1";
                }

                wrapper.append(label, input);
                fields.appendChild(wrapper);

                return input;
            }

            const nameInput = addField(
                "Название",
                service.name,
                "name"
            );

            const descriptionWrapper = document.createElement("label");
            descriptionWrapper.className = "service-admin-field";

            const descriptionLabel = document.createElement("span");
            descriptionLabel.textContent = "Описание";

            const descriptionInput = document.createElement("textarea");
            descriptionInput.name = "description";
            descriptionInput.value = service.description;
            descriptionInput.rows = 3;

            descriptionWrapper.append(
                descriptionLabel,
                descriptionInput
            );

            const priceSmall = addField(
                "Маленький автомобиль, ₽",
                service.price_small,
                "price_small",
                "number"
            );

            const priceMedium = addField(
                "Средний автомобиль, ₽",
                service.price_medium,
                "price_medium",
                "number"
            );

            const priceLarge = addField(
                "Большой автомобиль, ₽",
                service.price_large,
                "price_large",
                "number"
            );

            const duration = addField(
                "Продолжительность, минут",
                service.duration_minutes,
                "duration_minutes",
                "number"
            );

            const activeWrapper = document.createElement("label");
            activeWrapper.className = "service-active";

            const activeInput = document.createElement("input");
            activeInput.type = "checkbox";
            activeInput.checked = service.is_active;

            const activeText = document.createElement("span");
            activeText.textContent = "Услуга доступна для записи";

            activeWrapper.append(activeInput, activeText);

            const saveButton = document.createElement("button");
            saveButton.type = "button";
            saveButton.textContent = "Сохранить изменения";

            const message = document.createElement("p");
            message.className = "message";

            saveButton.addEventListener("click", async () => {
                const payload = {
                    name: nameInput.value.trim(),
                    description: descriptionInput.value.trim(),
                    price_small: Number(priceSmall.value),
                    price_medium: Number(priceMedium.value),
                    price_large: Number(priceLarge.value),
                    duration_minutes: Number(duration.value),
                    is_active: activeInput.checked
                };

                if (
                    !payload.name ||
                    !Number.isFinite(payload.price_small) ||
                    !Number.isFinite(payload.price_medium) ||
                    !Number.isFinite(payload.price_large) ||
                    !Number.isInteger(payload.duration_minutes) ||
                    payload.duration_minutes <= 0 ||
                    payload.price_small < 0 ||
                    payload.price_medium < 0 ||
                    payload.price_large < 0
                ) {
                    message.textContent = "Проверьте введённые значения.";
                    message.className = "message error";
                    return;
                }

                saveButton.disabled = true;
                message.textContent = "Сохраняем...";
                message.className = "message";

                try {
                    const response = await adminFetch(
                        `/api/admin/services/${service.id}`,
                        {
                            method: "PUT",
                            headers: {
                                "Content-Type": "application/json"
                            },
                            body: JSON.stringify(payload)
                        }
                    );

                    const data = await response.json();

                    if (!response.ok) {
                        throw new Error(
                            data.detail || "Не удалось сохранить услугу"
                        );
                    }

                    message.textContent = "Изменения сохранены.";
                    message.className = "message success";

                    heading.textContent = payload.name;

                } catch (error) {
                    message.textContent = error.message;
                    message.className = "message error";

                } finally {
                    saveButton.disabled = false;
                }
            });

            card.append(
                heading,
                code,
                fields,
                descriptionWrapper,
                activeWrapper,
                saveButton,
                message
            );

            container.appendChild(card);
        });

    } catch (error) {
        container.textContent = error.message;
    }
}

