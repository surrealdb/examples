'use client';

import React from "react";
import PoweredBy from '../../public/powered-by-surrealdb.svg';
import Image from "next/image";

export function Footer() {
    return (
        <div className="flex justify-between gap-16 py-24">
            <Image className="max-h-16 w-min" src={PoweredBy} alt="Powered by SurrealDB" />
        </div>
    )
}