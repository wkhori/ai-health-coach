"use client";

import { Button } from "@/components/ui/button";
import { patients, patientIds } from "@/lib/demo-data";
import { PhaseBadge } from "@/components/sidebar/phase-badge";
import { ChevronDown } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";

interface PatientSwitcherProps {
  currentPatientId: string;
  onSwitch: (id: string) => void;
}

export function PatientSwitcher({
  currentPatientId,
  onSwitch,
}: PatientSwitcherProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const current = patients[currentPatientId];

  return (
    <div className="relative" ref={ref}>
      <Button
        variant="outline"
        size="sm"
        className="gap-1.5"
        onClick={() => setOpen(!open)}
      >
        <span className="max-w-[120px] truncate">{current.name}</span>
        <ChevronDown
          className={cn("size-3 transition-transform", open && "rotate-180")}
        />
      </Button>
      {open && (
        <div className="absolute right-0 top-full z-50 mt-1 w-56 overflow-hidden rounded-lg border bg-popover p-1 shadow-md">
          <div className="px-2 py-1.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            Demo Patients
          </div>
          {patientIds.map((id) => {
            const p = patients[id];
            return (
              <button
                key={id}
                onClick={() => {
                  onSwitch(id);
                  setOpen(false);
                }}
                className={cn(
                  "flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors hover:bg-muted",
                  currentPatientId === id && "bg-muted"
                )}
              >
                <span className="flex-1 truncate">{p.name}</span>
                <PhaseBadge phase={p.phase} />
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
