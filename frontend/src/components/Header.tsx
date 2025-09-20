import shieldIcon from "@/assets/shield-icon.png";

const Header = () => {
  return (
    <header className="bg-card border-b border-border">
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-center space-x-3">
          <img 
            src={shieldIcon} 
            alt="CrisisClarity Shield" 
            className="w-8 h-8"
          />
          <div className="text-center">
            <h1 className="text-3xl font-bold text-foreground">CrisisClarity</h1>
            <p className="text-muted-foreground text-sm mt-1">
              Verify information. Fight misinformation. Stay informed.
            </p>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;