import type { Config } from "tailwindcss";

export default {
	content: ["./src/**/*.{html,js,svelte,ts}"],
	theme: {
		extend: {
			backgroundImage: {
				dots: "url('/background.svg')",
			},
			colors: {
				"purple-sticky": "#CA7FFF",
				"pink-sticky": "#FF7FCF",
				dark: "#282C38",
			},
			borderRadius: {
				"4xl": "25px",
			},
		},
	},
	safelist: ["text-red-600"],
	plugins: [],
} satisfies Config;
