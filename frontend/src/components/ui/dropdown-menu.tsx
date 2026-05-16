import * as React from "react"
import { cn } from "@/lib/utils"

interface DropdownMenuContextValue {
  open: boolean
  setOpen: (open: boolean) => void
}

const DropdownMenuContext = React.createContext<DropdownMenuContextValue | null>(null)

function useDropdownMenu() {
  const ctx = React.useContext(DropdownMenuContext)
  if (!ctx) throw new Error("DropdownMenu components must be used within <DropdownMenu>")
  return ctx
}

export function DropdownMenu({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = React.useState(false)
  return (
    <DropdownMenuContext.Provider value={{ open, setOpen }}>
      <div className="relative inline-block">{children}</div>
    </DropdownMenuContext.Provider>
  )
}

export function DropdownMenuTrigger({ children, asChild, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { asChild?: boolean; children: React.ReactNode }) {
  const { open, setOpen } = useDropdownMenu()
  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children as React.ReactElement<any>, {
      onClick: () => setOpen(!open),
    })
  }
  return (
    <button onClick={() => setOpen(!open)} {...props}>
      {children}
    </button>
  )
}

export function DropdownMenuContent({ children, className, align = "start", ...props }: React.HTMLAttributes<HTMLDivElement> & { align?: "start" | "end" }) {
  const { open, setOpen } = useDropdownMenu()
  const ref = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    if (open) document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [open, setOpen])

  if (!open) return null

  return (
    <div
      ref={ref}
      className={cn(
        "absolute z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md animate-in fade-in-0 zoom-in-95",
        align === "end" ? "right-0" : "left-0",
        "top-full mt-1",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export function DropdownMenuItem({ className, onClick, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  const { setOpen } = useDropdownMenu()
  return (
    <div
      className={cn(
        "relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground",
        className
      )}
      onClick={(e) => {
        onClick?.(e)
        setOpen(false)
      }}
      {...props}
    />
  )
}
