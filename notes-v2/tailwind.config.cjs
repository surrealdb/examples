/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
        './src/components/**/*.{js,ts,jsx,tsx,mdx}',
        './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            backgroundImage: {
                dots: "url('/background.svg')",
            },
            colors: {
                'purple-sticky': '#CA7FFF',
                'pink-sticky': '#FF7FCF',
                dark: '#282C38',
            },
            borderRadius: {
                '4xl': '25px',
            },
        },
    },
    safelist: ['text-red-600'],
    plugins: [],
};
