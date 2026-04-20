// javascript logic for app

document.addEventListener("DOMContentLoaded", () => {
  const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

  const errorMessage = document.getElementById("error-message");

  function authHeaders(json = false) {
    const headers = {};
    const token = localStorage.getItem("token");
    if (token) {
      headers["Authorization"] = "Bearer " + token;
    }
    if (json) {
      headers["Content-Type"] = "application/json";
    }
    return headers;
  }

  // Handle login form
  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = loginForm.elements["username"].value;
      const password = loginForm.elements["password"].value;

      try {
        const response = await fetch(`${API_BASE_URL}/users/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        });

        const data = await response.json();
        if (data.status === "success") {
          localStorage.setItem("token", data.bearer);
          if (data.role) {
            localStorage.setItem("role", data.role);
          }
          if (data.role === "doctor") {
            window.location.href = "doctor_dash.html";
          } else {
            window.location.href = "patient_dash.html";
          }
        } else if (errorMessage) {
          errorMessage.textContent = data.message || "Login failed.";
        }
      } catch (error) {
        console.error("Error during login:", error);
        if (errorMessage) {
          errorMessage.textContent = "An error occurred. Please try again.";
        }
      }
    });
  }

  // Handle register form
  const registerForm = document.getElementById("register-form");
  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const username = registerForm.elements["username"].value;
      const password = registerForm.elements["password"].value;
      const role = registerForm.elements["role"].value;

      try {
        const response = await fetch(`${API_BASE_URL}/users/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password, role }),
        });
        const data = await response.json();

        if (data.status === "success") {
          alert("Registration successful! Please log in.");
          window.location.href = "login.html";
        } else if (errorMessage) {
          errorMessage.textContent = data.message || "Registration failed.";
        }
      } catch (error) {
        console.error("Error during registration:", error);
        if (errorMessage) {
          errorMessage.textContent = "An error occurred. Please try again.";
        }
      }
    });
  }

  // Dashboard logic
  const dashboard = document.getElementById("dashboard");
  if (dashboard) {
    const token = localStorage.getItem("token");
    if (!token) {
      window.location.href = "login.html";
    } else {
      fetch(`${API_BASE_URL}/users/me`, {
        headers: { Authorization: "Bearer " + token },
      })
        .then((res) => {
          if (res.status === 403) {
            localStorage.removeItem("token");
            localStorage.removeItem("role");
            window.location.href = "login.html";
            throw new Error("Unauthorized");
          }
          return res.json();
        })
        .then((data) => {
          if (data.status === "success") {
            const userInfo = document.getElementById("user-info");
            if (userInfo) {
              userInfo.textContent = `Welcome, ${data.user.username}`;
            }
          }
        })
        .catch((error) => {
          console.error("Error fetching user:", error);
        });
    }
  }

  // Logout
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      localStorage.removeItem("token");
      localStorage.removeItem("role");
      window.location.href = "login.html";
    });
  }

  // Appointments
  const appointmentsList = document.getElementById("appointments-list");
  const appointmentForm = document.getElementById("appointment-form");
  const appointmentMessage = document.getElementById("appointment-message");

  async function loadAppointments() {
    if (!appointmentsList) return;

    try {
      const response = await fetch(`${API_BASE_URL}/appointments`, {
        method: "GET",
        headers: authHeaders(),
      });
      const data = await response.json();

      if (data.status !== "success") {
        appointmentsList.innerHTML = "<li>Error loading appointments.</li>";
        return;
      }
      if (!data.appointments || data.appointments.length === 0) {
        appointmentsList.innerHTML = "<li>No appointments found.</li>";
        return;
      }
      const role = localStorage.getItem("role");

      appointmentsList.innerHTML = data.appointments
        .map(
          (appt) => `
      <div class="appointment-card">
        <p><strong>Date:</strong> ${appt.appointment_date}</p>
        <p><strong>Time:</strong> ${appt.appointment_time}</p>
        <p><strong>With:</strong> ${appt.doctor_name || appt.patient_name || "N/A"}</p>
        <p><strong>Reason:</strong> ${appt.reason || "N/A"}</p>
        <p><strong>Status:</strong> ${appt.status}</p>
        ${
          role === "patient" && appt.status !== "cancelled"
            ? `
            <button onclick="cancelAppointment('${appt.appointment_id}')" 
              style="margin-top:10px; background:#dc3545; color:white; border:none; padding:8px 12px; border-radius:6px; cursor:pointer;">
              Cancel Appointment
            </button>`
            : ""
        }
      </div>
    `,
        )
        .join("");
    } catch (error) {
      appointmentsList.innerHTML =
        "<p>Server error while loading appointments.</p>";
    }
  }

  if (appointmentForm) {
    appointmentForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const appointment_date =
        appointmentForm.elements["appointment_date"].value;
      const appointment_time =
        appointmentForm.elements["appointment_time"].value;
      const reason = appointmentForm.elements["reason"].value;

      try {
        const response = await fetch(`${API_BASE_URL}/appointments`, {
          method: "POST",
          headers: authHeaders(true),
          body: JSON.stringify({ appointment_date, appointment_time, reason }),
        });
        const data = await response.json();
        if (data.status === "success") {
          if (appointmentMessage) {
            appointmentMessage.textContent =
              "Appointment scheduled successfully!";
            appointmentMessage.style.color = "green";
          }
          appointmentForm.reset();
          loadAppointments();
        } else {
          if (appointmentMessage) {
            appointmentMessage.textContent =
              data.message || "Failed to schedule appointment.";
            appointmentMessage.style.color = "red";
          }
        }
      } catch (error) {
        console.error("Error scheduling appointment:", error);
        if (appointmentMessage) {
          appointmentMessage.textContent =
            "An error occurred. Please try again.";
          appointmentMessage.style.color = "red";
        }
      }
    });
  }
  // visuals to cancel appointment
  window.cancelAppointment = async function (appointmentId) {
    if (!confirm("Are you sure you want to cancel this appointment?")) return;
    try {
      const response = await fetch(`${API_BASE_URL}/appointments`, {
        method: "DELETE",
        headers: authHeaders(true),
        body: JSON.stringify({ appointment_id: appointmentId }),
      });
      const data = await response.json();
      if (data.status === "success") {
        // find the button that was clicked and remove its parent card
        const button = document.querySelector(
          `button[onclick="cancelAppointment('${appointmentId}')"]`,
        );
        if (button) {
          button.closest(".appointment-card").remove();
        }
      } else {
        alert(data.message || "Failed to cancel appointment.");
      }
    } catch (error) {
      console.error("Error cancelling appointment:", error);
      alert("An error occurred. Please try again.");
    }
  };

  if (appointmentsList) {
    loadAppointments();
  }

  // Patient profile
  const profileName = document.getElementById("profile-name");
  const profileProvider = document.getElementById("profile-provider");
  const profileRole = document.getElementById("profile-role");
  const profilePatients = document.getElementById("profile-patients");

  if (profileName && profileProvider) {
    const token = localStorage.getItem("token");
    fetch(`${API_BASE_URL}/users/me`, {
      headers: { Authorization: "Bearer " + token },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "success") {
          profileName.textContent = data.user.username;
          if (profileRole) profileRole.textContent = data.user.role;
        }
      });

    fetch(`${API_BASE_URL}/users/assigned-doctor`, {
      headers: { Authorization: "Bearer " + token },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "success" && data.doctor) {
          profileProvider.textContent = data.doctor.username;
        } else {
          profileProvider.textContent = "No assigned doctor.";
        }
      });
  }

  // Doctor profile
  if (profileName && profilePatients) {
    const token = localStorage.getItem("token");
    fetch(`${API_BASE_URL}/users/me`, {
      headers: { Authorization: "Bearer " + token },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "success") {
          profileName.textContent = data.user.username;
        }
      });

    fetch(`${API_BASE_URL}/users/assigned-patients`, {
      headers: { Authorization: "Bearer " + token },
    })
      .then((res) => res.json())
      .then((data) => {
        if (
          data.status === "success" &&
          data.patients &&
          data.patients.length > 0
        ) {
          profilePatients.innerHTML = data.patients
            .map((p) => "<li>" + p.username + "</li>")
            .join("");
        } else {
          profilePatients.innerHTML = "<li>No assigned patients.</li>";
        }
      });
  }
});
