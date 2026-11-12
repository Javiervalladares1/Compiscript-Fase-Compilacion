// Salida: Toby ladra., Toby. Constructor heredado y despacho dinamico.
class Animal {
  let nombre: string;
  function constructor(nombre: string) {
    this.nombre = nombre;
  }
  function hablar(): string {
    return this.nombre + " hace ruido.";
  }
}
class Perro : Animal {
  function hablar(): string {
    return this.nombre + " ladra.";
  }
}
let animal: Animal = new Perro("Toby");
print(animal.hablar());
print(animal.nombre);
