import { useContext, createContext, JSX, createSignal, createEffect, onCleanup, Accessor, onMount } from "solid-js";
import Surreal from "surrealdb";
import { createMutation } from "@tanstack/solid-query";
import { createStore } from "solid-js/store";

interface SurrealProviderProps {
	children: JSX.Element;
	/** The database endpoint URL */
	endpoint: string;
	/** Optional existing Surreal client */
	client?: Surreal;
	/* Optional connection parameters */
	params?: Parameters<Surreal["connect"]>[1];
	/** Auto connect on component mount, defaults to true */
	autoConnect?: boolean;
}

interface SurrealProviderState {
	/** The Surreal instance */
	client: Accessor<Surreal>;
	/** Whether the connection is pending */
	isConnecting: Accessor<boolean>;
	/** Whether the connection was successfully established */
	isSuccess: Accessor<boolean>;
	/** Whether the connection rejected in an error */
	isError: Accessor<boolean>;
	/** The connection error, if present */
	error: Accessor<unknown|null>;
	/** Connect to the Surreal instance */
	connect: () => Promise<void>;
	/** Close the Surreal instance */
	close: () => Promise<true>;
}

interface SurrealProviderStore {
	instance: Surreal;
	status: "connecting" | "connected" | "disconnected";
}

const SurrealContext = createContext<SurrealProviderState>();

export function SurrealProvider(props: SurrealProviderProps) {

	const [store, setStore] = createStore<SurrealProviderStore>({ 
		instance: props.client ?? new Surreal(),
		status: "disconnected"
	});

	const { 
		mutateAsync,
		isError,
		error
	} = createMutation(() => ({
		mutationFn: async () => {
			setStore("status", "connecting");
			await store.instance.connect(props.endpoint, props.params);
		}
	}));

	onMount(() => {

		if(props.autoConnect) {
			mutateAsync();
		}

		store.instance.emitter.subscribe("connected", () => {
			setStore("status", "connected");
		});

		store.instance.emitter.subscribe("disconnected", () => {
			setStore("status", "disconnected");
		});
	});

	const providerValue: SurrealProviderState = {
		client: () => store.instance,
		close: () => store.instance.close(),
		connect: mutateAsync,
		error: () => error,
		isConnecting: () => store.status === "connecting",
		isError: () => isError,
		isSuccess: () => store.status === "connected"
	};

	return (
		<SurrealContext.Provider value={providerValue}>
			{store.status === "connected" && props.children}
		</SurrealContext.Provider>
	);
}

export function useSurreal(): SurrealProviderState {
	const context = useContext(SurrealContext);
	
	if(!context) {
		throw new Error("useSurreal must be used within a SurrealProvider");
	}

	return context;
}