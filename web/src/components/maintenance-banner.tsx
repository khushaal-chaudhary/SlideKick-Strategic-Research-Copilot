import { Wrench } from "lucide-react";
import { MAINTENANCE_MODE } from "@/lib/constants";

export function MaintenanceBanner() {
  if (!MAINTENANCE_MODE) return null;

  return (
    <div className="w-full border-b border-amber-500/30 bg-amber-500/10 px-4 py-2">
      <div className="container flex items-center justify-center gap-2 text-sm text-amber-700 dark:text-amber-400">
        <Wrench className="h-4 w-4 shrink-0" />
        <p>
          <span className="font-medium">Under maintenance:</span> the live demo
          backend is being upgraded, so queries may fail temporarily. The Tech
          Wiki and Metrics pages are unaffected.
        </p>
      </div>
    </div>
  );
}
