import type { LucideIcon } from "lucide-react";

interface Props {
  icon: LucideIcon;
  size?: number;
  label?: string;
}

export function Icon({ icon: IconComponent, size = 16, label }: Props) {
  return (
    <IconComponent
      size={size}
      aria-label={label}
      aria-hidden={label ? "false" : "true"}
    />
  );
}
