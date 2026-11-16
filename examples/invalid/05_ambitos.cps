// @expect SEM001 SEM004 SEM009 SEM001
// Uso de variables no declaradas y redeclaracion en el mismo ambito.
print(noExiste);
let repetida: integer = 1;
let repetida: integer = 2;
noDeclarada = 5;

{
  let interna: integer = 1;
}
print(interna);          // 'interna' ya salio de su ambito
