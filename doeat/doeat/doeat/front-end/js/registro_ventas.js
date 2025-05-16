window.addEventListener('load', () => {
  document.querySelectorAll('.carrusel').forEach(carrusel => {
    let index = 0;
    const imgs = carrusel.querySelectorAll('img');
    if (imgs.length > 0) {
      imgs.forEach(img => img.style.display = 'none');
      imgs[0].style.display = 'block'; // mostrar el primero al cargar
    }

    setInterval(() => {
      imgs.forEach(img => img.style.display = 'none');
      imgs[index].style.display = 'block';
      index = (index + 1) % imgs.length;
    }, 2000);
  });
});

  
  const formulario = document.getElementById('formulario');
  const tabla = document.getElementById('tablaFactura').querySelector('tbody');
  const totalDisplay = document.getElementById('total');
  
  let total = 0;
  
  formulario.addEventListener('submit', function (e) {
    e.preventDefault();
    agregarAFactura();
  });
  
  function agregarAFactura() {
    const producto = document.getElementById('producto').value.trim();
    const cantidad = parseInt(document.getElementById('cantidad').value);
  
    if (!producto || cantidad < 1) {
      alert('Por favor ingresa un producto y una cantidad válida.');
      return;
    }
  
    // Precio base aleatorio por demo
    const precioUnitario = obtenerPrecio(producto);
    const precioTotal = precioUnitario * cantidad;
  
    // Agregar a la tabla
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${producto}</td>
      <td>${cantidad}</td>
      <td>${precioTotal.toLocaleString()}</td>
    `;
    tabla.appendChild(row);
  
    // Sumar al total
    total += precioTotal;
    totalDisplay.textContent = `$${total.toLocaleString()}`;
  
    // Resetear campos
    formulario.reset();
    document.getElementById('cantidad').value = 1;
  }
  
  function obtenerPrecio(nombre) {
    // Simulación de precios base
    const precios = {
      'empanada': 4500,
      'pastel de pollo': 3500,
      'pastel de carne': 3500,
      'rollo de canela': 5000
    };
  
    return precios[nombre.toLowerCase()] || 4000; // Default
  }
  