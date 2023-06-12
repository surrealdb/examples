import { Navbar } from "@/components/navbar";
import "./globals.css";
import { Poppins } from "next/font/google";
import { Footer } from "@/components/footer";
import { cn } from "@/lib/utils";

const poppins = Poppins({ subsets: ["latin"], weight: ['100', '400', '900'] });

export const metadata = {
  title: "SurrealDB stickies",
  description: "Create, edit and remove stickies! Powered by SurrealDB!",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={cn(poppins.className, "h-screen flex flex-col bg-dots")}>
        <div className="mx-auto w-full max-w-screen-xl px-8 sm:px-24 flex-grow flex flex-col">
          <Navbar />
          <div className="flex-grow">
            {children}
          </div>
          <Footer />
        </div>
      </body>
    </html>
  );
}
