// Clases, constructor, herencia, constructor heredado y sobrescritura.
class Animal {
  let nombre: string;
  let edad: integer;

  function constructor(nombre: string) {
    this.nombre = nombre;
    this.edad = 0;
  }

  function hablar(): string {
    return this.nombre + " hace ruido.";
  }

  function cumplirAnios(): void {
    this.edad = this.edad + 1;
  }
}

class Perro : Animal {
  function hablar(): string {          // sobrescritura con firma compatible
    return this.nombre + " ladra.";
  }
}

let animal: Animal = new Animal("Generico");
let perro: Perro = new Perro("Rex");   // usa el constructor heredado
let comoBase: Animal = perro;          // subclase asignable a la base

perro.cumplirAnios();                  // metodo heredado
print(animal.hablar());
print(perro.hablar());
print(comoBase.nombre + " " + perro.edad);
