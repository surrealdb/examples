import { useSurreal } from "~/lib/providers/surrealdb";
import { NavbarAvatar } from "./avatar";
import { A } from "@solidjs/router";

export function Navbar() {

	const { } = useSurreal();

	return (
		<header class="p-4 flex justify-between shadow-md items-center">
			<A href="/">
				Home
			</A>
			<A href="/create">
				Create Poll
			</A>
			<NavbarAvatar />
		</header>
	);
}