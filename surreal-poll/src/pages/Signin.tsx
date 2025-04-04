import { useNavigate } from "@solidjs/router";
import { createSignal, JSX } from "solid-js";
import { Button } from "~/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "~/components/ui/card";
import { TextField, TextFieldInput, TextFieldLabel } from "~/components/ui/text-field";
import { useAuth } from "~/lib/providers/auth";

export function Signin(): JSX.Element {

	const { login } = useAuth();
	const navigate = useNavigate();

	const [email, setEmail] = createSignal("");
	const [password, setPassword] = createSignal("");

	const handleSubmit = async () => {

		try {
			await login(email(), password());
			navigate("/");
		} catch(e) {
			console.error(e);
		}
	};

	return (
		<Card>
		<CardHeader>
			<CardTitle>
				Signup for an account
			</CardTitle>
			<CardDescription>
				Enter your email and password to create an account
			</CardDescription>
		</CardHeader>
		<CardContent class="flex flex-col gap-y-8">
			<TextField>
				<TextFieldLabel>
					Email
				</TextFieldLabel>
				<TextFieldInput 
					value={email()}
					type="email" 
					onChange={(e) => setEmail(e.target.value)}
				/>
			</TextField>
			<TextField>
				<TextFieldLabel>
					Password
				</TextFieldLabel>
				<TextFieldInput
					value={password()} 
					type="password" 
					onChange={(e) => setPassword(e.target.value)}
				/>
			</TextField>
			<Button onClick={handleSubmit}>
				Signin
			</Button>
		</CardContent>
	</Card>
	);
}