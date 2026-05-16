import * as React from "react"
import { cn } from "@/lib/utils"

interface DialogContextValue {
  open: boolean
  setOpen: (open: boolean) => void
}

const DialogContext = React.createContext<DialogContextValue | null>(null)

function useDialog() {
  const ctx = React.useContext(DialogContext)
  if (!ctx) throw new Error("Dialog components must be used within <Dialog>")
  return ctx
}

export function Dialog({ open: controlledOpen, onOpenChange, children }: { open?: boolean; onOpenChange?: (open: boolean) => void; children: React.ReactNode }) {
  const [internalOpen, setInternalOpen] = React.useState(false)
  const open = controlledOpen ?? internalOpen
  const setOpen = (v: boolean) => {
    setInternalOpen(v)
    onOpenChange?.(v)
  }
  return <DialogContext.Provider value={{ open, setOpen }}>{children}</DialogContext.Provider>
}

export function DialogTrigger({ children, asChild, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { asChild?: boolean; children: React.ReactNode }) {
  const { setOpen } = useDialog()
  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children as React.ReactElement<any>, {
      onClick: () => setOpen(true),
    })
  }
  return <button onClick={() => setOpen(true)} {...props}>{children}</button>
}

export function DialogContent({ children, className }: { children: React.ReactNode; className?: string }) {
  const { open, setOpen } = useDialog()
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/80" onClick={() => setOpen(false)} />
      <div className={cn("relative z-50 w-full max-w-lg rounded-lg border bg-background p-6 shadow-lg", className)}>
        {children}
        <button
          className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100"
          onClick={() => setOpen(false)}
        >
          &times;
        </button>
      </div>
    </div>
  )
}

export function DialogHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col space-y-1.5 text-center sm:text-left", className)} {...props} />
}

export function DialogTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h2 className={cn("text-lg font-semibold leading-none tracking-tight", className)} {...props} />
}

export function DialogDescription({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn("text-sm text-muted-foreground", className)} {...props} />
}
