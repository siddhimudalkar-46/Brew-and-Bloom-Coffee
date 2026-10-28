/* Brew & Bloom Coffee — frontend + Flask API integration */
document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("mobile-toggle");
  const nav = document.getElementById("nav-links");
  const menuIcon = document.getElementById("menu-icon");

  if (toggle && nav) {
    toggle.setAttribute("aria-expanded", "false");
    toggle.addEventListener("click", () => {
      const isOpen = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(isOpen));
      if (menuIcon) {
        menuIcon.classList.toggle("fa-bars", !isOpen);
        menuIcon.classList.toggle("fa-xmark", isOpen);
      }
    });
    nav.querySelectorAll("a").forEach(link => link.addEventListener("click", () => {
      nav.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
      if (menuIcon) {
        menuIcon.classList.add("fa-bars");
        menuIcon.classList.remove("fa-xmark");
      }
    }));
  }

  let toastTimer;
  let toast = document.querySelector(".toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.className = "toast";
    toast.setAttribute("role", "status");
    toast.setAttribute("aria-live", "polite");
    document.body.appendChild(toast);
  }
  function showToast(message) {
    toast.textContent = message;
    toast.classList.add("show");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toast.classList.remove("show"), 3500);
  }

  // Order buttons now create an order in SQLite through the Flask API.
  document.querySelectorAll(".order-btn").forEach(button => {
    button.addEventListener("click", async () => {
      const card = button.closest(".menu-card");
      const itemName = card?.querySelector(".item-name")?.textContent.trim();
      if (!itemName) return;

      try {
        const response = await fetch("/api/menu");
        if (!response.ok) throw new Error("Could not load the menu.");
        const items = await response.json();
        const item = items.find(entry => entry.name === itemName);
        if (!item) throw new Error("This item is currently unavailable.");

        const customerName = prompt(`Place an order for ${item.name}\nPrice: $${Number(item.price).toFixed(2)}\n\nEnter your name:`);
        if (customerName === null) return;
        const customerEmail = prompt("Enter your email address:");
        if (customerEmail === null) return;
        const quantityText = prompt("Quantity (1–20):", "1");
        if (quantityText === null) return;
        const quantity = Number(quantityText);
        if (!Number.isInteger(quantity) || quantity < 1 || quantity > 20) {
          showToast("Please enter a whole-number quantity from 1 to 20.");
          return;
        }

        button.disabled = true;
        const orderResponse = await fetch("/api/orders", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            customer_name: customerName,
            customer_email: customerEmail,
            item_id: item.id,
            quantity
          })
        });
        const result = await orderResponse.json();
        if (!orderResponse.ok) throw new Error(result.error || "Order could not be saved.");
        showToast(`Order #${result.order_id} saved! Total: $${Number(result.total).toFixed(2)}. Thank you!`);
      } catch (error) {
        showToast(error.message || "Could not place the order. Please try again.");
      } finally {
        button.disabled = false;
      }
    });
  });

  // Contact form submits to Flask and is stored in SQLite.
  const form = document.getElementById("contact-form");
  const feedback = document.getElementById("form-feedback");
  if (form && feedback) {
    form.addEventListener("submit", async event => {
      event.preventDefault();
      feedback.textContent = "";
      feedback.className = "form-feedback";
      const name = form.querySelector("#name")?.value.trim() || "";
      const email = form.querySelector("#email")?.value.trim() || "";
      const message = form.querySelector("#message")?.value.trim() || "";

      try {
        const response = await fetch("/api/contact", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, email, message })
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Message could not be saved.");
        feedback.textContent = "Thank you! Your message has been saved.";
        feedback.classList.add("success");
        form.reset();
      } catch (error) {
        feedback.textContent = error.message || "Something went wrong. Please try again.";
        feedback.classList.add("error");
      }
    });
  }

  const sections = document.querySelectorAll("section[id]");
  const navLinks = document.querySelectorAll(".nav-link");
  if ("IntersectionObserver" in window && sections.length && navLinks.length) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          navLinks.forEach(link => {
            const active = link.getAttribute("href") === `#${entry.target.id}`;
            link.classList.toggle("active", active);
            if (active) link.setAttribute("aria-current", "page");
            else link.removeAttribute("aria-current");
          });
        }
      });
    }, { rootMargin: "-30% 0px -60% 0px" });
    sections.forEach(section => observer.observe(section));
  }
});
