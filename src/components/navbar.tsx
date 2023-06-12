'use client';

import React from "react";
import Logo from '../../public/logo.svg';
import { AddSticky } from "./add-sticky";
import Image from "next/image";

export function Navbar() {
    return (
        <div className="flex flex-col md:flex-row justify-between gap-8 sm:gap-16 py-20">
            <Image className="max-h-16 w-min" src={Logo} alt="SurrealDB Stickies logo" />

            <div className="flex gap-4">
                <AddSticky color="pink" />
                <AddSticky color="purple" />
            </div>
        </div>
    )
}