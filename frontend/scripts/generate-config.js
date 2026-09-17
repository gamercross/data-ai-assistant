// Vercel 빌드 시 환경 변수 API_BASE_URL 값을 읽어 js/config.js를 생성합니다.
// Vercel 프로젝트 설정 > Environment Variables 에서 API_BASE_URL을 Render 배포 URL로 지정하세요.
const fs = require("fs");
const path = require("path");

const apiBaseUrl = process.env.API_BASE_URL || "http://localhost:8000";
const outPath = path.join(__dirname, "..", "js", "config.js");
const content = `window.API_BASE_URL = ${JSON.stringify(apiBaseUrl)};\n`;

fs.writeFileSync(outPath, content);
console.log(`generated ${outPath} -> API_BASE_URL=${apiBaseUrl}`);
