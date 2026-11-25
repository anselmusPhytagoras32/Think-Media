// Apply the saved appearance before the application renders, including on reload.
try {
  document.documentElement.dataset.theme = localStorage.getItem("thinkmedia.theme.v1") === "dark" ? "dark" : "light";
} catch {
  document.documentElement.dataset.theme = "light";
}
