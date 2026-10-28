document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("buscadorProductos");
  const products = document.querySelectorAll(".item-producto");

  if (!searchInput) {
    return;
  }

  searchInput.addEventListener("input", () => {
    const query = searchInput.value.toLowerCase().trim();

    products.forEach((product) => {
      const name = product.getAttribute("data-nombre") || "";
      product.hidden = !name.includes(query);
    });
  });
});
