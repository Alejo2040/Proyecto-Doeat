document.addEventListener("DOMContentLoaded", () => {
  fetch("../../../../prediccion_mes.json")
    .then(response => response.json())
    .then(data => {
      const ordenado = data.sort((a, b) => b.cantidad_predicha - a.cantidad_predicha);
      const contenedorMes = document.getElementById("predicciones-mes");
      contenedorMes.innerHTML = "";

      // Mostrar los dos productos más predichos visualmente
      ordenado.slice(0, 2).forEach(p => {
        
        const nombreImagen = p.producto.toLowerCase().replace(/\s+/g, "_") + ".png";
        const carpeta = p.producto.toLowerCase().includes("croissant") || p.producto.toLowerCase().includes("pastel") ? "Reposteria" : "Bebidas";
        const div = document.createElement("div");
        div.className = "producto img-text";

        div.innerHTML = `
          <img src="../img/${carpeta}/${nombreImagen}" alt="${p.producto}">
          <p>${p.producto}<br><strong>${p.cantidad_predicha} estimados</strong></p>
        `;
        contenedorMes.appendChild(div);
      });

      // Gráfica circular con los 7 productos más predichos
      const ctx = document.getElementById("ventasChart").getContext("2d");
      const top7 = ordenado.slice(0, 7);

      const etiquetas = top7.map(p => p.producto);
      const cantidades = top7.map(p => p.cantidad_predicha);

      new Chart(ctx, {
        type: 'pie', 
        data: {
          labels: etiquetas,
          datasets: [{
            label: 'Predicción de Ventas (unidades)',
            data: cantidades,
            backgroundColor: [
              '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
              '#9966FF', '#FF9F40', '#C9CBCF'
            ],
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: 'right' 
            },
            
          }
        }
      });
    })
    .catch(err => {
      console.error("Error cargando el archivo JSON:", err);
      document.getElementById("predicciones-mes").innerText = "Error al cargar predicciones.";
    });
});




