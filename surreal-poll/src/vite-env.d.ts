/// <reference types="vite/client" />

interface ImportMetaEnv {
	readonly VITE_DB_HOST: string;
	readonly VITE_DB_USER: string;
	readonly VITE_DB_PASS: string;
}

interface ImportMeta {
	readonly env: ImportMetaEnv;
}