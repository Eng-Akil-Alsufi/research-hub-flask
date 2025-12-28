// Auto-hide alerts after 5 seconds
document.addEventListener("DOMContentLoaded", () => {
  const alerts = document.querySelectorAll(".alert")

  alerts.forEach((alert) => {
    setTimeout(() => {
      alert.style.transition = "opacity 0.5s ease"
      alert.style.opacity = "0"
      setTimeout(() => {
        alert.remove()
      }, 500)
    }, 5000)
  })
})

// Confirm delete actions
document.querySelectorAll('a[href*="delete"]').forEach((link) => {
  link.addEventListener("click", (e) => {
    if (!confirm("هل أنت متأكد من الحذف؟")) {
      e.preventDefault()
    }
  })
})

// Form validation
document.querySelectorAll("form").forEach((form) => {
  form.addEventListener("submit", (e) => {
    const requiredFields = form.querySelectorAll("[required]")
    let isValid = true

    requiredFields.forEach((field) => {
      if (!field.value.trim()) {
        isValid = false
        field.style.borderColor = "#dc3545"
      } else {
        field.style.borderColor = "#e0e0e0"
      }
    })

    if (!isValid) {
      e.preventDefault()
      alert("يرجى ملء جميع الحقول المطلوبة")
    }
  })
})