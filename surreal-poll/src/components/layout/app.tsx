import { RouteSectionProps } from "@solidjs/router";
import { Navbar } from "../Navbar";
import { useAuth } from "~/lib/providers/auth";

export function AppLayout(props: RouteSectionProps) {

	const { user } = useAuth();

	return (
		<>
			<Navbar />
			<div class="mx-auto pt-28 px-8 max-w-sm sm:max-w-md md:max-w-lg lg:max-w-xl xl:max-w-2xl">
				{props.children}
			</div>
			{JSON.stringify(user() ?? '{ user: "not" }')}
		</>
	);
}