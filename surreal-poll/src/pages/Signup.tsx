import { useNavigate } from "@solidjs/router";
import { createSignal, JSX } from "solid-js";
import { Button } from "~/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "~/components/ui/card";
import { TextField, TextFieldInput, TextFieldLabel } from "~/components/ui/text-field";
import { useAuth } from "~/lib/providers/auth";

export function Signup(): JSX.Element {

	const navigate = useNavigate();
	const { register } = useAuth();

	const [name, setName] = createSignal("");
	const [email, setEmail] = createSignal("");
	const [password, setPassword] = createSignal("");
	const [confirmPassword, setConfirmPassword] = createSignal("");
	const [error, setError] = createSignal<string>();

	const handleSubmit = async () => {

		if(password() !== confirmPassword()) {
			setError("Passwords do not match");
			return;
		}

		try {
			await register({ 
				name: name(),
				email: email(),
				pass: password(),
			});

			navigate("/signin");
		} catch(e) {
			setError("An error occurred while creating your account");
		}
	}

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
						Name
					</TextFieldLabel>
					<TextFieldInput 
						value={name()} 
						type="text" 
						onChange={(e) => setName(e.target.value)} 
					/>
				</TextField>
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
				<TextField>
					<TextFieldLabel>
						Confirm Password
					</TextFieldLabel>
					<TextFieldInput
						value={confirmPassword()} 
						type="password" 
						onChange={(e) => setConfirmPassword(e.target.value)}
					/>
				</TextField>
				<Button onClick={handleSubmit}>
					Signup
				</Button>
			</CardContent>
		</Card>
	);
}