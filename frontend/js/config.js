// One place to decide where the API lives.
//  - Deployed (Flask serves frontend + API from one domain): "/api"
//  - Local dev (Live Server / file:// ) : http://localhost:5000/api
// To point the frontend at a different backend, set
//   window.FASHIONHUB_API_URL = "https://your-backend.example.com/api";
// in a <script> tag BEFORE this file.
const API_BASE_URL = (() => {
  if (window.FASHIONHUB_API_URL) return window.FASHIONHUB_API_URL;
  const { protocol, hostname, port } = window.location;
  const isLocal = hostname === "localhost" || hostname === "127.0.0.1";
  if (protocol === "file:" || (isLocal && port !== "5000")) {
    return "http://localhost:5000/api";
  }
  return "/api";
})();
