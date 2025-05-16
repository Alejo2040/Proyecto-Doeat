document.addEventListener('DOMContentLoaded', () => {
  const inventario = JSON.parse(localStorage.getItem('inventario')) || [];
  inventario.forEach(item => agregarFila(item.ingrediente, item.cantidad));
});

document.getElementById('ingredienteForm').addEventListener('submit', function (e) {
  e.preventDefault();

  const ingrediente = document.getElementById('ingrediente').value;
  const cantidad = parseInt(document.getElementById('cantidadIngrediente').value);

  if (ingrediente && cantidad > 0) {
    agregarFila(ingrediente, cantidad);
    guardarIngrediente(ingrediente, cantidad);

    document.getElementById('ingrediente').value = '';
    document.getElementById('cantidadIngrediente').value = '';
  }
});

function agregarFila(ingrediente, cantidad) {
  const tabla = document.querySelector('#tablaInventario tbody');
  const fila = document.createElement('tr');

  fila.innerHTML = `
    <td>${ingrediente}</td>
    <td>${cantidad}</td>
    <td>
      <button onclick="editarFila(this)">Editar</button>
      <button onclick="eliminarFila(this)">Eliminar</button>
    </td>
  `;

  tabla.appendChild(fila);
}

function guardarIngrediente(ingrediente, cantidad) {
  const inventario = JSON.parse(localStorage.getItem('inventario')) || [];
  inventario.push({ ingrediente, cantidad });
  localStorage.setItem('inventario', JSON.stringify(inventario));
}

function eliminarFila(btn) {
  const fila = btn.parentElement.parentElement;
  const ingrediente = fila.children[0].textContent;
  fila.remove();
  eliminarDeStorage(ingrediente);
}

function editarFila(btn) {
  const fila = btn.parentElement.parentElement;
  const viejoNombre = fila.children[0].textContent;
  const nuevoIngrediente = prompt("Nuevo nombre del ingrediente:", viejoNombre);
  const nuevaCantidad = prompt("Nueva cantidad:", fila.children[1].textContent);

  if (nuevoIngrediente && !isNaN(nuevaCantidad)) {
    fila.children[0].textContent = nuevoIngrediente;
    fila.children[1].textContent = nuevaCantidad;

    actualizarEnStorage(viejoNombre, nuevoIngrediente, parseInt(nuevaCantidad));
  }
}

function eliminarDeStorage(nombre) {
  let inventario = JSON.parse(localStorage.getItem('inventario')) || [];
  inventario = inventario.filter(item => item.ingrediente !== nombre);
  localStorage.setItem('inventario', JSON.stringify(inventario));
}

function actualizarEnStorage(nombreViejo, nombreNuevo, cantidadNueva) {
  let inventario = JSON.parse(localStorage.getItem('inventario')) || [];
  const index = inventario.findIndex(item => item.ingrediente === nombreViejo);
  if (index !== -1) {
    inventario[index] = { ingrediente: nombreNuevo, cantidad: cantidadNueva };
    localStorage.setItem('inventario', JSON.stringify(inventario));
  }
}
