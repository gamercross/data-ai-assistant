// 로컬 개발 시 자동으로 localhost 백엔드를 사용하고,
// 배포 환경에서는 scripts/generate-config.js가 이 파일을 빌드 시점에 덮어씁니다 (vercel.json 참고).
window.API_BASE_URL = (() => {
  const isLocal = ["localhost", "127.0.0.1"].includes(window.location.hostname);
  return isLocal ? "http://localhost:8000" : "https://data-ai-assistant-api.onrender.com";
})();
