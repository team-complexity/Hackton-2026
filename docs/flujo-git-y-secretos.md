# Flujo de Git y manejo de secretos

Reglas para trabajar en este repositorio. **El repo es público**: todo lo que se sube, incluido el historial de commits, lo puede ver cualquiera para siempre.

Responsable: Hugo coordina la seguridad; cada quien une su propio pull request, y Juan y Leonel revisan lo que entra a `main`. Issue: #16. Roles y calendario: [flujo-de-trabajo.md](../flujo-de-trabajo.md).

## 1. Regla de oro: los secretos nunca van al repositorio

Son secretos:

- La API key de pey (`PEY_API_KEY`).
- El secreto del webhook de pey (`PEY_WEBHOOK_SECRET`).
- Tokens y secretos de WhatsApp, base de datos y sesiones (`WHATSAPP_*`, `DATABASE_URL`, `SECRET_KEY`).
- CLABEs, contraseñas y cualquier dato personal de alguien real.

Dónde **sí** van:

| Lugar | Para qué |
|---|---|
| `backend/.env` (en tu computadora) | Desarrollo local. Git lo ignora gracias a `.gitignore` |
| Variables de entorno del hosting | La demo en vivo |

Dónde **nunca** van: código, commits, issues, pull requests, comentarios, capturas de pantalla, README ni grupos de chat.

Las reglas del hackathon lo exigen: las credenciales del API de pey no pueden estar en repos públicos ni en código del cliente (la web). La web **nunca** llama a pey directamente; todo pasa por el backend.

## 2. Cómo configurar tu `.env`

```bash
cd backend
cp .env.example .env
```

Rellena los valores en `.env`. Si agregas una variable nueva, agrégala **vacía** también en `.env.example` para que el resto sepa que existe.

## 3. Cómo compartir un secreto con el equipo

- Solo con quien lo necesita para su issue.
- Por mensaje privado (nunca en el grupo) o, mejor, con un gestor de contraseñas (Bitwarden, 1Password).
- Las credenciales de pey son por proyecto y no se pueden compartir con personas ajenas al equipo ni usar en otro proyecto.

## 4. Ramas

- `main` siempre debe funcionar. **Nadie sube directo a `main`.**
- Una rama por issue: `feature/<número>-<descripcion-corta>`.
  - Ejemplos: `feature/62-endpoint-qr`, `feature/64-pagina-cobro`.
  - Para errores: `fix/<número>-<descripcion>`.

```bash
git checkout main
git pull
git checkout -b feature/62-endpoint-qr
# ... trabajas y haces commits ...
git push -u origin feature/62-endpoint-qr
```

## 5. Pull requests

1. Abre el pull request hacia `main` y escribe `Closes #<número>` en la descripción para que el issue se cierre solo.
2. Llena la descripción con la [plantilla de pull request](../.github/pull_request_template.md): qué pedía el issue, qué se hizo, qué se decidió y por qué, cómo probarlo, qué quedó pendiente y la revisión de seguridad. No hay otro documento aparte.
3. Antes de unir, revisa tu propio diff y busca llaves, `.env` o datos personales.
4. Únelo tú a `main` cuando el CI esté en verde y cumpla los criterios de aceptación del issue. No hace falta aprobación previa.
5. Juan y Leonel revisan lo que entra a `main`. Si algo salió mal, lo comentan en el pull request o abren un issue `tipo: bug`. Si rompe la demo, se corrige o se revierte con otro pull request.

## 6. Si GitHub bloquea tu `git push`

El repo tiene **Push protection** activado: si un commit contiene algo que parece una llave, GitHub rechaza el push con un mensaje parecido a este:

```
remote: error: GH013: Repository rule violations found
remote: - Push cannot contain secrets
remote:   — Commit: a1b2c3d   Path: backend/app/config.py:12
```

**Qué significa:** el push no se hizo, así que **la llave no llegó a GitHub** y no hay que rotarla. Pero sigue dentro de tu commit local; aunque la borres en un commit nuevo, el viejo la sigue teniendo y GitHub lo volverá a bloquear. Hay que reescribir el commit.

**Si la llave está en tu último commit:**

```bash
# 1. Quita la llave del archivo y pásala a backend/.env
# 2. Rehaz el commit sin la llave:
git add .
git commit --amend --no-edit
git push
```

**Si está en un commit anterior:**

```bash
# Deshace tus commits locales pero conserva los cambios en tus archivos
git reset --soft origin/main
# Quita la llave del archivo y pásala a backend/.env
git add .
git commit -m "Descripción de tu cambio"
git push
```

(Si tu rama ya existía en GitHub, usa `origin/<tu-rama>` en lugar de `origin/main`, y si te lo pide, `git push --force-with-lease`.)

**No uses el enlace "allow secret"** que ofrece GitHub, salvo que estés seguro de que es un falso positivo (un texto que parece llave pero no lo es). Si tienes dudas, pregunta a Hugo, que coordina la seguridad.

## 7. Si una llave se filtra

Una llave está filtrada si llegó a GitHub, a un chat, a una captura o a cualquier lugar público.

1. **Rótala de inmediato:** en https://portal.mipey.mx → Desarrollador, genera una llave nueva o rota el secreto del webhook y borra la vieja.
2. **Avisa a pey en menos de 24 horas.** Las reglas del hackathon lo exigen.
3. Actualiza la llave nueva en el `.env` de quien la use y en las variables del hosting.
4. Avisa al equipo y a Hugo, que coordina la seguridad.

Borrar el archivo o el commit **no basta**: el historial de Git, los forks y las copias en caché pueden conservarla.

## 8. Lo que ya está activado en el repo

- `.gitignore` ignora `.env`, `.env.*` (salvo `.env.example`), llaves `*.pem` y `*.key`.
- **Secret scanning:** GitHub detecta llaves conocidas en el repositorio.
- **Push protection:** bloquea los pushes que contienen llaves.
- **Dependabot alerts:** avisa si una librería que usamos tiene una vulnerabilidad conocida.
- **Rama `main` protegida:** solo se puede cambiar con un pull request.
